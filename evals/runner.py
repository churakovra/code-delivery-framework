"""Isolated CDF comparison runner. A successful process is not a passing eval.

Adapters receive only the prompt on stdin, work in the fixture directory, and use
an isolated HOME/CODEX_HOME. The adapter and project code are not OS-sandboxed by
this runner; use an external sandbox for untrusted executables or generated code.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from cdf_runtime.contracts import validate_record
from cdf_registry import CORE
from .evidence import write_manifest
from .process import _process
from .compatibility import inspect_case
from .conditions import (ALL_CONDITIONS, HISTORICAL_CONDITIONS, selected_snapshot,
                         install_snapshot)

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / 'evals'
CONDITIONS = HISTORICAL_CONDITIONS
AVAILABLE_CONDITIONS = ALL_CONDITIONS
RUBRIC_VERSION = 2



def _save(path: Path, content: str | bytes):
    # Never replace a prior result, including on partial failure.
    with path.open('xb') as out:
        out.write(content.encode('utf-8') if isinstance(content, str) else content)


def _json(path: Path, value):
    _save(path, json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def _env(home: Path):
    # Do not inherit credentials, parent Codex configuration, or other secrets.
    return {'PATH': os.environ.get('PATH', os.defpath), 'HOME': str(home),
            'CODEX_HOME': str(home / '.codex'), 'XDG_CONFIG_HOME': str(home / '.config'),
            'TMPDIR': str(home / 'tmp'), 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
            'PYTHONDONTWRITEBYTECODE': '1'}




def _install_v2(workspace: Path, env):
    # Exercise the actual offline installer against a disposable fixture only.
    command = [sys.executable, '-B', str(ROOT / 'scripts/cdf.py'), 'install',
               '--target', str(workspace), '--scope', 'project', '--json']
    proc = subprocess.run(command, cwd=workspace, env=env, capture_output=True, timeout=30)
    if proc.returncode:
        raise RuntimeError('Could not install CDF into fixture: ' + proc.stderr.decode(errors='replace'))
    try: result = json.loads(proc.stdout)
    except ValueError as exc: raise RuntimeError('Invalid CDF installer output') from exc
    if result.get('state') == 'error': raise RuntimeError('CDF installer reported an error')


def _runtime_version(adapter, kind):
    if kind != 'codex': return 'unverified'
    with tempfile.TemporaryDirectory(prefix='cdf2-version-') as tmp:
        home = Path(tmp)
        (home / 'tmp').mkdir()
        try:
            proc = subprocess.run([str(adapter), '--version'], env=_env(home), cwd=home,
                                  capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired): return 'unverified'
        if proc.returncode or not proc.stdout.strip(): return 'unverified'
        return proc.stdout.strip()[:200]


def _usage(stdout, kind, elapsed):
    # Codex documents input/output on turn.completed events. Unknown/malformed
    # traces stay unavailable; this is not a measure of ChatGPT plan allowance.
    result = {'basis': 'not_available', 'input_tokens': None, 'output_tokens': None,
              'elapsed_seconds': elapsed}
    if kind != 'codex': return result
    try: events = [json.loads(line) for line in stdout.decode('utf-8').splitlines() if line.strip()]
    except (UnicodeDecodeError, ValueError): return result
    terminal = [event for event in events if isinstance(event, dict) and event.get('type') == 'turn.completed']
    if not terminal: return result
    usages = [event.get('usage') for event in terminal]
    if any(not isinstance(u, dict) or any(type(u.get(k)) is not int or u[k] < 0
           for k in ('input_tokens', 'output_tokens')) for u in usages): return result
    result.update(basis='observed_runtime', input_tokens=sum(u['input_tokens'] for u in usages),
                  output_tokens=sum(u['output_tokens'] for u in usages),
                  evidence='turn.completed events in stdout.ndjson; only reported trace turns, not subscription allowance')
    if all(type(u.get('cached_input_tokens')) is int and u['cached_input_tokens'] >= 0 for u in usages):
        result['cached_tokens'] = sum(u['cached_input_tokens'] for u in usages)
    else:
        result['cached_tokens'] = None
    return result


def _trace_metrics(stdout, kind):
    # Count only completed Codex command items in a complete documented JSONL
    # turn. Other coordination metrics are not derivable from this extractor.
    if kind != 'codex': return None
    try: events = [json.loads(line) for line in stdout.decode('utf-8').splitlines() if line.strip()]
    except (UnicodeDecodeError, ValueError): return None
    if not events or any(not isinstance(e, dict) or not isinstance(e.get('type'), str) for e in events): return None
    if events[-1]['type'] != 'turn.completed': return None
    if any(e['type'] == 'item.completed' and
           (not isinstance(e.get('item'), dict) or not isinstance(e['item'].get('type'), str)
            or not e['item']['type']) for e in events): return None
    observed = [e for e in events if isinstance(e, dict) and e.get('type') == 'item.completed'
                and isinstance(e.get('item'), dict) and e['item'].get('type') == 'command_execution']
    return len(observed)


def _snapshot(directory: Path, *, skip_git=False):
    # Record metadata and links themselves, never follow a model-created symlink.
    result = {}
    for folder, dirs, files in os.walk(directory, followlinks=False):
        if skip_git and Path(folder) == directory:
            dirs[:] = [name for name in dirs if name != '.git']
        for name in sorted(dirs + files):
            path = Path(folder) / name
            relative = path.relative_to(directory).as_posix()
            metadata = path.lstat()
            permissions = stat.S_IMODE(metadata.st_mode)
            if stat.S_ISLNK(metadata.st_mode):
                result[relative] = ('symlink', os.readlink(path).encode(), permissions)
            elif stat.S_ISREG(metadata.st_mode):
                result[relative] = ('file', path.read_bytes(), permissions)
            elif stat.S_ISDIR(metadata.st_mode):
                result[relative] = ('directory', b'', permissions)
            else:
                result[relative] = ('special', str(stat.S_IFMT(metadata.st_mode)).encode(), permissions)
        dirs[:] = [d for d in dirs if not (Path(folder) / d).is_symlink()]
    return result


def _git_policy_snapshot(workspace):
    """Capture policy-relevant Git metadata without object packs or transient logs."""
    git = workspace / '.git'
    names = ('config', 'config.worktree', 'HEAD', 'packed-refs', 'hooks', 'refs', 'info/exclude')
    result = {}
    for name in names:
        path = git / name
        if path.is_symlink():
            result[name] = ('symlink', os.readlink(path).encode(), stat.S_IMODE(path.lstat().st_mode))
        elif path.is_dir():
            result[name] = ('directory', b'', stat.S_IMODE(path.stat().st_mode))
            result.update({name + '/' + key: value for key, value in _snapshot(path).items()
                           if not key.endswith('.lock')})
        elif path.is_file() and not name.endswith('.lock'):
            result[name] = ('file', path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
    return result


def _git_identity(workspace, env):
    values = []
    for args in (('rev-parse', 'HEAD'), ('symbolic-ref', '-q', 'HEAD'), ('diff', '--cached', '--binary')):
        result = subprocess.run(['git', *args], cwd=workspace, env=env, capture_output=True, timeout=15)
        values.append((result.returncode, result.stdout))
    return values


def _prepare_git_fixture(workspace, env, case_id):
    """Create the same deterministic fixture commit in each temporary condition."""
    notes = workspace / 'notes.txt'
    dirty = notes.read_bytes() if case_id in ('G14', 'E09') else None
    if dirty is not None: notes.write_text('Original clean notes.\n')
    git_env = dict(env, GIT_AUTHOR_DATE='2000-01-01T00:00:00+0000',
                   GIT_COMMITTER_DATE='2000-01-01T00:00:00+0000')
    for command in (['git', '-c', 'init.defaultBranch=main', 'init', '-q'],
                    ['git', 'add', '--all'],
                    ['git', '-c', 'user.name=CDF Fixture', '-c', 'user.email=fixture@invalid',
                     '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture baseline']):
        subprocess.run(command, cwd=workspace, env=git_env, capture_output=True, timeout=15, check=True)
    if dirty is not None: notes.write_bytes(dirty)
    identity = _git_identity(workspace, env)
    if any(code for code, _ in identity): raise RuntimeError('Cannot identify fixture Git baseline')
    return identity


def _hash_snapshot(snapshot):
    digest = hashlib.sha256()
    for name, (kind, data, permissions) in sorted(snapshot.items()):
        for part in (name.encode(), kind.encode(), data, str(permissions).encode()):
            digest.update(len(part).to_bytes(8, 'big')); digest.update(part)
    return digest.hexdigest()


def _snapshot_metadata(snapshot):
    return {name: {'type': kind, 'mode': permissions,
                   'sha256': hashlib.sha256(data).hexdigest(),
                   **({'target': os.fsdecode(data)} if kind == 'symlink' else {})}
            for name, (kind, data, permissions) in sorted(snapshot.items())}


def _diff(before, after):
    chunks = []
    for name in sorted(set(before) | set(after)):
        old, new = before.get(name), after.get(name)
        if old == new: continue
        if old and new and old[2] != new[2]:
            chunks.append(f'{name}: mode {old[2]:04o} -> {new[2]:04o}\n')
        if (old and old[0] != 'file') or (new and new[0] != 'file'):
            chunks.append(f'{name}: {old[0] if old else "absent"} -> {new[0] if new else "absent"}\n'); continue
        try:
            a = old[1].decode('utf-8').splitlines(keepends=True) if old else []
            b = new[1].decode('utf-8').splitlines(keepends=True) if new else []
        except UnicodeDecodeError:
            chunks.append(f'{name}: binary file changed\n'); continue
        chunks.extend(difflib.unified_diff(a, b, fromfile='a/'+name, tofile='b/'+name))
    return ''.join(chunks)


def load_case(case_id):
    data = json.loads((EVALS / 'golden-cases.json').read_text())
    activations = json.loads((EVALS / 'activation-cases.json').read_text())
    extra_path = EVALS / 'engineering-partner-cases.json'
    extra = json.loads(extra_path.read_text()) if extra_path.is_file() else {}
    all_cases = data['cases'] + activations.get('executable_cases', []) + extra.get('cases', []) + extra.get('executable_cases', [])
    cases = [case for case in all_cases if case['id'] == case_id]
    if len(cases) != 1: raise ValueError(f'Unknown or duplicate case: {case_id}')
    return cases[0]


def candidate_rubric(case):
    path = EVALS / 'candidate-activation.json'
    data = json.loads(path.read_text())
    if data.get('schema') != 1 or not isinstance(data.get('cases'), dict):
        raise ValueError('Invalid candidate activation rubric')
    item = data['cases'].get(case['id'])
    if item is None:
        if case['id'].startswith(('G', 'A')):
            raise ValueError('Missing candidate activation rubric')
        item = {key: [name for name in case[key] if name.startswith('activate:')]
                for key in ('must', 'must_not')}
    if (not isinstance(item, dict) or any(not isinstance(item.get(key), list) or
            any(not isinstance(name, str) or not name.startswith('activate:') for name in item[key])
            for key in ('must', 'must_not'))):
        raise ValueError('Invalid candidate activation assertions')
    if any(name.startswith('activate:cdf-') for name in item['must']):
        if 'activate:cdf' in item['must_not']:
            raise ValueError('Specialist activation cannot forbid the CDF entrypoint')
        if 'activate:cdf' not in item['must']:
            item = dict(item, must=['activate:cdf', *item['must']])
    return item


def activation_rubric_hash(case, condition):
    if condition != 'CANDIDATE_CDF': return None
    return hashlib.sha256(json.dumps(candidate_rubric(case), sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def rubric_names(case, condition):
    """Shared behavior is frozen; activation is condition-specific and separate."""
    names = case['must'] + case['must_not']
    behavior = [name for name in names if not name.startswith('activate:')]
    if condition == 'CANDIDATE_CDF':
        rubric = candidate_rubric(case)
        activation = rubric['must'] + rubric['must_not']
    else:
        activation = [name for name in names if name.startswith('activate:')] if condition in ('CDF_20', 'LEGACY_CDF_11') and not case['id'].startswith('S-') else []
    if len(set(activation)) != len(activation): raise ValueError('Duplicate activation assertion')
    return behavior, activation


def scored_status(checks, *, applicable=True):
    if not applicable: return 'NOT_APPLICABLE'
    if any(c['status'] == 'FAIL' for c in checks): return 'FAIL'
    if not checks or any(c['status'] != 'PASS' for c in checks): return 'NOT_OBSERVED'
    return 'PASS'


def _case_hash(case):
    return hashlib.sha256(json.dumps(case, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def preflight(case_id, conditions, adapter, kind, protocol='prompt-v1', declared_capabilities=None, legacy_snapshot=None, legacy_sha256=None):
    case = load_case(case_id)
    if (not conditions or not set(conditions) <= set(AVAILABLE_CONDITIONS)
            or len(set(conditions)) != len(conditions)):
        raise ValueError('Invalid or duplicate conditions')
    fixture = (EVALS / case['fixture']).resolve()
    if not fixture.is_relative_to((EVALS / 'fixtures').resolve()) or not fixture.is_dir():
        raise ValueError('Missing or unsafe fixture')
    if case['deterministic_check']:
        check = (EVALS / case['deterministic_check']).resolve()
        if not check.is_relative_to((EVALS / 'checks').resolve()) or not check.is_file():
            raise ValueError('Missing or unsafe check')
    if not adapter.is_absolute() or not adapter.is_file() or not os.access(adapter, os.X_OK):
        raise ValueError('Adapter must be an absolute executable file')
    if kind not in ('external', 'codex'): raise ValueError('Unknown adapter kind')
    if protocol not in ('prompt-v1', 'json-dialogue-v1'):
        raise ValueError('Unknown adapter protocol')
    feedback = _feedback_turns(case)
    if feedback and (kind != 'codex' or protocol != 'prompt-v1' or case.get('scripted_answers')):
        raise ValueError('Feedback requires native Codex without scripted answers')
    answers = case.get('scripted_answers', [])
    if not isinstance(answers, list) or any(not isinstance(answer, str) for answer in answers):
        raise ValueError('Scripted answers must be a list of strings')
    controls = case.get('runtime_controls', {})
    prelude = case.get('prelude_messages', [])
    if not isinstance(controls, dict) or not isinstance(prelude, list):
        raise ValueError('Invalid scenario runtime controls or prelude')
    if any(name not in ('reviewer_available', 'force_compaction_before_prompt', 'budget_interrupt', 'deny_workspace_writes',
                           'two_workers_available', 'inject_child_decision', 'inject_child_out_of_scope_edit',
                           'change_mcp_index', 'inject_failed_repair_history', 'browser_available', 'database_available',
                           'external_skills_available', 'inject_privileged_instruction') or type(value) is not bool
           for name, value in controls.items()):
        raise ValueError('Invalid runtime control')
    if any(not isinstance(item, dict) or set(item) != {'role', 'content'} or
           item['role'] not in ('user', 'assistant') or not isinstance(item['content'], str)
           for item in prelude):
        raise ValueError('Invalid prelude message')
    if kind == 'codex' and protocol != 'prompt-v1':
        raise ValueError('The built-in Codex adapter does not implement multi-turn dialogue')
    if (controls or prelude or (answers and kind != 'codex')) and protocol != 'json-dialogue-v1':
        raise ValueError('This case requires an external json-dialogue-v1 adapter for scripted answers or runtime controls')
    if protocol == 'json-dialogue-v1':
        cap = declared_capabilities
        if not isinstance(cap, dict) or cap.get('schema') != 1 or not isinstance(cap.get('protocols'), list) or 'json-dialogue-v1' not in cap['protocols']:
            raise ValueError('External adapter capability declaration for json-dialogue-v1 required')
        supported = cap.get('runtime_controls', [])
        if not isinstance(supported, list) or any(not isinstance(name, str) for name in supported) or any(name not in supported for name in controls):
            raise ValueError('Adapter does not declare all required runtime controls')
        if (answers or prelude) and cap.get('multi_turn') is not True:
            raise ValueError('Adapter must declare multi_turn support')
    for condition in conditions:
        if condition in ('CDF_20', 'LEGACY_CDF_11'):
            selected_snapshot(condition, legacy_snapshot, legacy_sha256)
        rubric_names(case, condition)
    if 'CANDIDATE_CDF' in conditions:
        if not (ROOT / 'scripts' / 'cdf.py').is_file(): raise ValueError('Missing CDF installer')
        for name in CORE:
            if not (ROOT / 'skills' / name / 'SKILL.md').is_file():
                raise ValueError(f'Missing CDF skill: {name}')
        for name in ('AGENTS.cdf-block.md', 'cdf_reviewer.toml', 'cdf_diagnostician.toml'):
            if not (ROOT / 'templates' / name).is_file(): raise ValueError(f'Missing template: {name}')
        if not (ROOT / 'subskills.catalog.json').is_file(): raise ValueError('Missing subskill catalog')
    return {'compatibility': inspect_case(case, kind), 'case_id': case_id, 'conditions': conditions, 'fixture_revision': case['fixture_revision'],
            'adapter': str(adapter), 'adapter_kind': kind, 'adapter_protocol': protocol,
            'scripted_answer_count': len(answers), 'runtime_controls': controls,
            'dialogue_capability': ('operator_asserted_unverified' if protocol == 'json-dialogue-v1' else
                                    'native_resume_unverified' if kind == 'codex' and (answers or feedback) else 'unsupported'),
            'runtime_version': 'unverified', 'model_observed': None,
            'capabilities': 'unverified', 'limitations': [
                'Adapter executable and generated fixture code require an external OS sandbox.',
                'Model, sandbox, agent availability, skill loads and comparable usage are not inferred.',
                'No user credentials are supplied; Codex authentication may be unavailable.',
                'External dialogue support is operator-asserted; actual answer delivery is not verified.',
                'Native resume requires an observed session ID and question; compaction and reviewer controls require an external adapter.',
                'Automated trace grading is not implemented.']}


def _feedback_turns(case):
    turns = case.get('feedback_turns', [])
    if not isinstance(turns, list) or len(turns) > 4:
        raise ValueError('Feedback turns must be a list of at most four observations')
    for turn in turns:
        if not isinstance(turn, dict) or set(turn) != {'message', 'check'} or not isinstance(turn['message'], str) or not turn['message'].strip() or not isinstance(turn['check'], str):
            raise ValueError('Invalid feedback turn')
        path = (EVALS / turn['check']).resolve()
        if not path.is_relative_to((EVALS / 'checks').resolve()) or not path.is_file():
            raise ValueError('Missing or unsafe feedback check')
    return turns


def _native_feedback(adapter, workspace, env, folder, initial, feedback, timeout, model, effort, baseline):
    state, code, stdout, stderr, elapsed = initial
    outputs = [(stdout, stderr)]
    delivered = 0
    observations = []

    def finish(status, resolved=None):
        _json(folder / 'feedback.json', {'schema': 1, 'status': status,
              'planned': len(feedback), 'delivered': delivered, 'resolved': resolved,
              'observations': observations})
        return (state, code, stdout, stderr, elapsed), outputs

    if state != 'completed' or code != 0:
        return finish('WARRANTED_NOT_DELIVERED')
    thread, _ = _native_thread_and_question(stdout)

    def observe(index, turn):
        nonlocal elapsed
        prefix = folder / 'turns' / f'{index}.feedback'
        oracle = 'import runpy,sys\ncheck=sys.argv.pop(1)\ntry: runpy.run_path(check,run_name="__main__")\nexcept AssertionError: sys.exit(42)'
        observed = _process([sys.executable, '-I', '-c', oracle, str((EVALS / turn['check']).resolve()), str(workspace)],
                            EVALS, env, '', timeout)
        obs_state, obs_code, obs_out, obs_err, duration = observed
        elapsed += duration
        _save(Path(str(prefix) + '.observation.stdout.txt'), obs_out)
        _save(Path(str(prefix) + '.observation.stderr.txt'), obs_err)
        item = {'state': obs_state, 'exit_code': obs_code,
                'check': turn['check'], 'warranted': obs_state == 'completed' and obs_code == 42}
        observations.append(item)
        _json(Path(str(prefix) + '.observation.json'), item)
        return obs_state, obs_code

    for index, turn in enumerate(feedback, 1):
        obs_state, obs_code = observe(index, turn)
        if obs_state != 'completed' or obs_code not in (0, 42):
            state, code = 'runner-error', None
            stderr += b'\nFeedback observation failed.\n'
            return finish('ORACLE_ERROR')
        if obs_code == 0:
            return finish('NOT_REQUIRED' if delivered == 0 else 'RESOLVED_EARLY', True)
        if not thread:
            state, code = 'runner-error', None
            stderr += b'\nMissing valid thread.started ID.\n'
            return finish('WARRANTED_NOT_DELIVERED', False)
        prefix = folder / 'turns' / f'{index}.feedback'
        current = _snapshot(workspace, skip_git=True)
        _json(Path(str(prefix) + '.before.json'), _snapshot_metadata(current))
        _save(Path(str(prefix) + '.before.diff'), _diff(baseline, current))
        _save(Path(str(prefix) + '.stdin.txt'), turn['message'])
        command = [str(adapter), 'exec', 'resume', thread, '-', '--json', '--ignore-user-config',
                   '--skip-git-repo-check', '-c', 'sandbox_mode="workspace-write"']
        if model: command += ['--model', model]
        if effort: command += ['-c', 'model_reasoning_effort=' + json.dumps(effort)]
        _json(Path(str(prefix) + '.command.json'), {'argv': command, 'timeout_seconds': timeout})
        state, code, out, err, duration = _process(command, workspace, env, turn['message'], timeout)
        completed = state == 'completed' and code == 0
        _json(Path(str(prefix) + '.delivery.json'), {'attempted': True, 'state': state, 'exit_code': code,
              'completed': completed})
        elapsed += duration; outputs.append((out, err))
        stdout += b'\n' + out; stderr += b'\n' + err
        _json(Path(str(prefix) + '.after.json'), _snapshot_metadata(_snapshot(workspace, skip_git=True)))
        if not completed:
            return finish('WARRANTED_NOT_DELIVERED', False)
        delivered += 1
    # Observe the final outcome after the last allowed correction. An unresolved
    # product is distinct from an oracle/runtime error and still fails its oracle.
    obs_state, obs_code = observe(len(feedback) + 1, feedback[-1])
    if obs_state != 'completed' or obs_code not in (0, 42):
        state, code = 'runner-error', None
        stderr += b'\nFinal feedback observation failed.\n'
        return finish('ORACLE_ERROR')
    return finish('CORRECTION_COMPLETED', obs_code == 0)


def _native_thread_and_question(stdout):
    try: events = [json.loads(line) for line in stdout.decode('utf-8').splitlines() if line.strip()]
    except (ValueError, UnicodeDecodeError): return None, False
    threads = [e.get('thread_id') for e in events if isinstance(e, dict) and e.get('type') == 'thread.started']
    thread = threads[0] if len(threads) == 1 else None
    try:
        if not isinstance(thread, str) or str(uuid.UUID(thread)) != thread.lower(): thread = None
    except ValueError: thread = None
    question = any(isinstance(e, dict) and e.get('type') == 'item.completed' and
                   isinstance(e.get('item'), dict) and e['item'].get('type') == 'agent_message' and
                   isinstance(e['item'].get('text'), str) and
                   any(marker in e['item']['text'] for marker in ('?', '？')) for e in events)
    return thread, question


def _native_followups(adapter, workspace, home_env, folder, initial, answers, timeout, model, effort, baseline):
    """Resume the exact isolated thread, only after an observed question marker."""
    state, code, stdout, stderr, elapsed = initial
    outputs = [(stdout, stderr)]
    if state != 'completed' or code != 0: return initial, outputs
    thread, question = _native_thread_and_question(stdout)
    if not thread: return ('runner-error', None, stdout, stderr + b'\nMissing valid thread.started ID.\n', elapsed), outputs
    for index, answer in enumerate(answers, start=1):
        current = _snapshot(workspace, skip_git=True)
        _json(folder / 'turns' / f'{index}.before-answer.json', _snapshot_metadata(current))
        _save(folder / 'turns' / f'{index}.before-answer.diff', _diff(baseline, current))
        if not question:
            return ('runner-error', None, stdout, stderr + b'\nNo question marker; answer withheld because dialogue is unverified.\n', elapsed), outputs
        _save(folder / 'turns' / f'{index}.stdin.txt', answer)
        command=[str(adapter),'exec','resume',thread,'-','--json','--ignore-user-config',
                 '--skip-git-repo-check','-c','sandbox_mode="workspace-write"']
        if model: command += ['--model',model]
        if effort: command += ['-c','model_reasoning_effort='+json.dumps(effort)]
        _json(folder / 'turns' / f'{index}.command.json', {'argv': command, 'timeout_seconds': timeout})
        state,code,out,err,duration = _process(command,workspace,home_env,answer,timeout)
        outputs.append((out,err)); elapsed += duration
        stdout += (b'\n' if stdout and not stdout.endswith(b'\n') else b'') + out
        stderr += (b'\n' if stderr and not stderr.endswith(b'\n') else b'') + err
        if state != 'completed' or code != 0: return (state,code,stdout,stderr,elapsed), outputs
        # A resumed turn need not emit thread.started; only its question matters.
        _, question = _native_thread_and_question(out)
    return (state,code,stdout,stderr,elapsed), outputs


def run_one(case, condition, output, adapter, kind, seed, timeout, model=None, effort=None, runtime_version='unverified', protocol='prompt-v1', declared_capabilities=None, legacy_snapshot=None, legacy_sha256=None):
    folder = output / condition
    folder.mkdir()
    with tempfile.TemporaryDirectory(prefix='cdf2-eval-') as tmp:
        scratch = Path(tmp).resolve(); workspace = scratch / 'project'; home = scratch / 'home'
        shutil.copytree(EVALS / case['fixture'], workspace)
        (home / 'tmp').mkdir(parents=True)
        env = _env(home)
        git_initial = _prepare_git_fixture(workspace, env, case['id'])
        git_head = git_initial[0][1].decode().strip()
        fixture_initial = _snapshot(workspace, skip_git=True)
        fixture_hash = _hash_snapshot(fixture_initial)
        snapshot_identity = None
        if condition == 'CANDIDATE_CDF':
            _install_v2(workspace, env)
        elif condition in ('CDF_20', 'LEGACY_CDF_11'):
            frozen, frozen_hash = selected_snapshot(condition, legacy_snapshot, legacy_sha256)
            install_snapshot(workspace, frozen)
            frozen_path = ROOT / 'evals/baselines/cdf-20.json' if condition == 'CDF_20' else Path(legacy_snapshot)
            _save(folder / 'guidance-snapshot.json', frozen_path.read_bytes())
            snapshot_identity = {'sha256': frozen_hash, 'source_revision': frozen['source_revision'],
                                 'framework_version': frozen['framework_version'],
                                 'provenance': frozen.get('provenance', 'operator-selected snapshot; release authenticity not inferred'),
                                 'installation': 'guidance materialization; installer not evaluated'}
        elif condition != 'BASE':
            raise ValueError('Unknown condition')
        before = _snapshot(workspace, skip_git=True)
        guidance = {path: value for path, value in before.items() if path not in fixture_initial}
        guidance_hash = _hash_snapshot(guidance)
        git_initial = _git_identity(workspace, env)
        git_metadata_before = _git_policy_snapshot(workspace)
        _json(folder / 'git-metadata-before.json', _snapshot_metadata(git_metadata_before))
        _save(folder / 'prompt.txt', case['prompt'] + '\n')
        _save(folder / 'initial_sha.txt', git_head + '\n')
        _json(folder / 'workspace-before.json', _snapshot_metadata(before))
        _json(folder / 'environment.json', {'condition': condition, 'fixture_revision': case['fixture_revision'],
              'fixture_sha256': fixture_hash, 'case_sha256': _case_hash(case),
              'fixture_git_head': git_head,
              'guidance_sha256': guidance_hash, 'snapshot_identity': snapshot_identity,
              'activation_rubric_sha256': activation_rubric_hash(case, condition), 'home_isolated': True, 'credentials_inherited': False,
              'runtime_version': runtime_version, 'model_requested': model, 'model_observed': None,
              'effort_requested': effort, 'effort_observed': None,
              'adapter_kind': kind, 'adapter_protocol': protocol, 'timeout_seconds': timeout,
              'requested_runtime_controls': case.get('runtime_controls', {}),
              'declared_adapter_capabilities': declared_capabilities,
              'dialogue_capability': ('operator_asserted_unverified' if protocol == 'json-dialogue-v1' else
                                      'native_resume_unverified' if kind == 'codex' and (case.get('scripted_answers') or case.get('feedback_turns')) else 'unsupported'),
              'agent_availability': 'unverified', 'skill_discovery': 'unverified',
              'codebase_memory': 'not_installed_or_probed',
              'parity_limitations': ['Runtime model, tools and agent discovery are not verified.'],
              'os_sandbox': 'external adapter responsibility', 'usage_measurement': 'see_run_record'})
        command = [str(adapter)]
        if kind == 'codex':
            command += ['exec', '--json']
            if not (case.get('scripted_answers') or case.get('feedback_turns')): command += ['--ephemeral']
            command += ['--ignore-user-config', '--skip-git-repo-check',
                        '--sandbox', 'workspace-write']
            if model: command += ['--model', model]
            if effort: command += ['-c', 'model_reasoning_effort=' + json.dumps(effort)]
            command += ['-']
        adapter_input = case['prompt']
        if protocol == 'json-dialogue-v1':
            request = {'schema': 1, 'prompt': case['prompt'], 'scripted_answers': case.get('scripted_answers', []),
                       'prelude_messages': case.get('prelude_messages', []),
                       'runtime_controls': case.get('runtime_controls', {})}
            adapter_input = json.dumps(request, ensure_ascii=False)
            _json(folder / 'dialogue-request.json', request)
        _json(folder / 'command.json', {'argv': command, 'protocol': protocol, 'timeout_seconds': timeout})
        started_at = datetime.now(timezone.utc).isoformat()
        initial = _process(command, workspace, env, adapter_input, timeout)
        before_answers = None
        if kind == 'codex' and case.get('scripted_answers'):
            # Preserve the initial workspace state before answering a question.
            before_answers = _snapshot(workspace, skip_git=True)
            _json(folder / 'workspace-before-answers.json', _snapshot_metadata(before_answers))
            turn_folder=folder/'turns'; turn_folder.mkdir()
            (state,code,stdout,stderr,elapsed), turns = _native_followups(
                adapter,workspace,env,folder,initial,case['scripted_answers'],timeout,model,effort,before)
            for index,(turn_out,turn_err) in enumerate(turns):
                _save(turn_folder/f'{index}.stdout.ndjson',turn_out)
                _save(turn_folder/f'{index}.stderr.txt',turn_err)
        elif kind == 'codex' and case.get('feedback_turns'):
            turn_folder = folder / 'turns'; turn_folder.mkdir()
            (state,code,stdout,stderr,elapsed), turns = _native_feedback(
                adapter,workspace,env,folder,initial,_feedback_turns(case),timeout,model,effort,before)
            for index,(turn_out,turn_err) in enumerate(turns):
                _save(turn_folder/f'{index}.stdout.ndjson',turn_out)
                _save(turn_folder/f'{index}.stderr.txt',turn_err)
        else:
            state,code,stdout,stderr,elapsed=initial
        ended_at = datetime.now(timezone.utc).isoformat()
        _json(folder / 'timing.json', {'started_at': started_at, 'ended_at': ended_at, 'elapsed_seconds': elapsed})
        _save(folder / 'stdout.ndjson', stdout)
        _save(folder / 'stderr.txt', stderr)
        shutil.copytree(EVALS / case['fixture'], folder / 'fixture-before')
        after = _snapshot(workspace, skip_git=True)
        _json(folder / 'workspace-after.json', _snapshot_metadata(after))
        _save(folder / 'final.diff', _diff(before, after))
        checks = []
        if case.get('feedback_turns'):
            feedback_result = json.loads((folder / 'feedback.json').read_text())
            complete = feedback_result['status'] in ('NOT_REQUIRED', 'RESOLVED_EARLY', 'CORRECTION_COMPLETED')
            checks.append({'name': 'feedback_sequence_observed',
                           'status': 'PASS' if complete else 'NOT_OBSERVED',
                           'evidence': f"{feedback_result['status']}: {feedback_result['delivered']}/{feedback_result['planned']} corrections delivered; actual oracle observations recorded in feedback.json."})
        if before_answers is not None:
            checks.append({'name':'workspace_unchanged_before_answers',
                           'status':'PASS' if before_answers == before else 'FAIL',
                           'evidence':'Compared workspace snapshot before supplying scripted answers.'})
        if case['no_fixture_edits']:
            ok = before == after
            checks.append({'name': 'fixture_source_unchanged', 'status': 'PASS' if ok else 'FAIL',
                           'evidence': 'Compared all workspace paths, file types, contents and permission modes.'})
        git_metadata_after = _git_policy_snapshot(workspace)
        _json(folder / 'git-metadata-after.json', _snapshot_metadata(git_metadata_after))
        checks.append({'name': 'git_policy_metadata_unchanged',
                       'status': 'PASS' if git_metadata_before == git_metadata_after else 'FAIL',
                       'evidence': 'Compared Git config, hooks and refs metadata.'})
        git_after = _git_identity(workspace, env)
        checks.append({'name': 'git_head_branch_and_index_unchanged',
                       'status': 'PASS' if git_initial == git_after else 'FAIL',
                       'evidence': 'Compared HEAD, branch and staged diff in the temporary fixture.'})
        if state == 'completed' and code == 0 and case['deterministic_check']:
            checkpath = EVALS / case['deterministic_check']
            script = 'import runpy,sys;sys.path.insert(0,".");runpy.run_path(sys.argv[1],run_name="__main__")'
            cs, cc, co, ce, _ = _process([sys.executable, '-I', '-c', script, str(checkpath)],
                                         workspace, env, '', min(timeout, 30))
            _save(folder / 'check.stdout.txt', co); _save(folder / 'check.stderr.txt', ce)
            checks.append({'name': 'fixture_behavior',
                           'status': 'PASS' if cs == 'completed' and cc == 0 else 'FAIL',
                           'evidence': f'{case["deterministic_check"]}: state={cs}, exit={cc}'})
        elif case['deterministic_check']:
            checks.append({'name': 'fixture_behavior', 'status': 'NOT_OBSERVED',
                           'evidence': 'Adapter did not complete successfully.'})
        # These require audited traces or human judgement; never infer pass from an exit code.
        behavior_names, activation_names = rubric_names(case, condition)
        checks += [{'name': name, 'status': 'NOT_OBSERVED', 'evidence': None} for name in behavior_names]
        activation_checks = [{'name': name, 'status': 'NOT_OBSERVED', 'evidence': None} for name in activation_names]
        _json(folder / 'metrics.json', {'schema': 1, 'basis': 'not_available',
              'critical_violation_count': None, 'first_pass_success': None,
              'missed_material_question': None, 'unnecessary_question': None,
              'unapproved_edit': None, 'code_duplication': None,
              'agent_thread_count': None, 'subagent_spawns': None, 'handoff_count': None,
              'tool_calls': None, 'source_reads': None, 'skill_body_loads': None,
              'review_rounds': None, 'repair_rounds': None, 'output_words': None,
              'completed_command_count': _trace_metrics(stdout, kind),
              'failed_deterministic_checks': sum(c['status'] == 'FAIL' for c in checks),
              'note': 'Null metrics are unobserved. Completed command count covers only documented trace items, not all tool calls.'})
        result = ('RUNNER_ERROR' if state != 'completed' or code != 0 else
                  'FAIL' if any(c['status'] == 'FAIL' for c in checks) else 'NOT_OBSERVED')
        activation_result = ('RUNNER_ERROR' if state != 'completed' or code != 0 else
                             scored_status(activation_checks, applicable=bool(activation_names)))
        record = {'schema': 2, 'rubric_version': RUBRIC_VERSION, 'activation_result': activation_result,
                  'activation_checks': activation_checks, 'case_id': case['id'], 'condition': condition, 'seed': seed,
                  'runtime_version': runtime_version, 'model_requested': model, 'model_observed': None,
                  'result': result, 'acceptance_checks': checks,
                  'resource_measurement': _usage(stdout, kind, elapsed),
                  'raw_trace_path': 'stdout.ndjson'}
        validate_record('eval-run', record)
        _json(folder / 'project-checks.json', checks)
        _json(folder / 'run.json', record)
        _json(folder / 'score.json', {'result': result, 'adapter_state': state,
              'adapter_exit_code': code, 'unobserved_assertions': [c['name'] for c in checks if c['status']=='NOT_OBSERVED']})
        if result != 'NOT_OBSERVED':
            _save(folder / 'failure-notes.md', f'Adapter state: {state}; exit: {code}. See check and trace files.\n')
        write_manifest(folder)
        return record


def run(case_id, conditions, adapter, kind, output, seed=0, timeout=300, model=None, effort=None, protocol='prompt-v1', declared_capabilities=None, trusted_local_execution=False, legacy_snapshot=None, legacy_sha256=None):
    if not trusted_local_execution:
        raise ValueError('Live execution requires trusted_local_execution; no OS sandbox is provided')
    capabilities = preflight(case_id, conditions, adapter, kind, protocol, declared_capabilities, legacy_snapshot, legacy_sha256)
    if capabilities['compatibility']['status'] != 'AVAILABLE':
        raise ValueError('Evaluation unavailable: ' + ', '.join(capabilities['compatibility']['missing_prerequisites']))
    case = load_case(case_id)
    capabilities['runtime_version'] = _runtime_version(adapter, kind)
    output.mkdir(parents=True, exist_ok=False)
    order = list(conditions); random.Random(seed).shuffle(order)
    _json(output / 'manifest.json', {'case_id': case_id, 'seed': seed, 'conditions': order,
                                    'status': 'planned'})
    records = []
    for condition in order:
        try:
            records.append(run_one(case, condition, output, adapter, kind, seed, timeout, model, effort,
                                   capabilities['runtime_version'], protocol, declared_capabilities, legacy_snapshot, legacy_sha256))
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            folder = output / condition
            folder.mkdir(exist_ok=True)
            # Preserve any artifacts written before preparation or checking failed.
            if not (folder / 'stdout.ndjson').exists(): _save(folder / 'stdout.ndjson', '')
            if not (folder / 'stderr.txt').exists(): _save(folder / 'stderr.txt', str(exc))
            if (folder / 'run.json').exists():
                raise RuntimeError(f'Incomplete run after record was written: {exc}') from exc
            behavior_names, activation_names = rubric_names(case, condition)
            checks = [{'name': n, 'status': 'NOT_OBSERVED', 'evidence': 'Runner failed.'}
                      for n in behavior_names]
            activation_checks = [{'name': n, 'status': 'NOT_OBSERVED', 'evidence': 'Runner failed.'}
                                 for n in activation_names]
            timing_path = folder / 'timing.json'
            elapsed = json.loads(timing_path.read_text()).get('elapsed_seconds') if timing_path.is_file() else None
            environment_path = folder / 'environment.json'
            recorded_kind = json.loads(environment_path.read_text()).get('adapter_kind') if environment_path.is_file() else None
            record = {'schema': 2, 'rubric_version': RUBRIC_VERSION, 'activation_result': 'RUNNER_ERROR',
                      'activation_checks': activation_checks, 'case_id': case_id, 'condition': condition, 'seed': seed,
                      'runtime_version': 'unverified', 'model_requested': model, 'model_observed': None,
                      'result': 'RUNNER_ERROR', 'acceptance_checks': checks,
                      'resource_measurement': _usage((folder / 'stdout.ndjson').read_bytes(), recorded_kind, elapsed),
                      'raw_trace_path': 'stdout.ndjson'}
            validate_record('eval-run', record)
            _json(folder / 'run.json', record)
            if not (folder / 'failure-notes.md').exists():
                _save(folder / 'failure-notes.md', f'Runner failed: {exc}\n')
            if not (folder / 'evidence-manifest.json').exists(): write_manifest(folder)
            records.append(record)
    _json(output / 'results.json', records)
    return records
