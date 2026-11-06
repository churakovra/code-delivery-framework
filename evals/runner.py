"""Isolated CDF comparison runner. A successful process is not a passing eval.

Adapters receive only the prompt on stdin, work in the fixture directory, and use
an isolated HOME/CODEX_HOME. The adapter and project code are not OS-sandboxed by
this runner; use an external sandbox for untrusted executables or generated code.
"""
from __future__ import annotations

import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import random
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid
from datetime import datetime, timezone
from cdf_runtime.contracts import validate_record

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / 'evals'
BASELINE = '3ff534627e8b10de3dba2c6443855e870567ef84'
CONDITIONS = ('BASE', 'CDF_06', 'CDF_20')
RUBRIC_VERSION = 2
CORE = ('cdf-backend', 'cdf-code-review', 'cdf-codebase-research', 'cdf-debugging',
        'cdf-documentation', 'cdf-frontend', 'cdf-implementation', 'cdf-orchestration',
        'cdf-planning', 'cdf-requirements', 'cdf-ui-design', 'cdf-verification')


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


def _process(command, cwd, env, prompt, timeout):
    started = time.monotonic()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            proc = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                    stdout=out, stderr=err, start_new_session=True)
            try:
                proc.communicate(prompt.encode(), timeout=timeout)
                state, code = 'completed', proc.returncode
            except subprocess.TimeoutExpired:
                try: os.killpg(proc.pid, signal.SIGKILL)
                except (ProcessLookupError, AttributeError): proc.kill()
                proc.communicate()
                state, code = 'timeout', None
        except OSError as exc:
            state, code = 'runner-error', None
            err.write(str(exc).encode())
        out.seek(0); err.seek(0)
        return state, code, out.read(), err.read(), round(time.monotonic() - started, 3)


def _safe_archive(destination: Path):
    # The source is immutable git content, never the changing working tree.
    result = subprocess.run(['git', 'archive', BASELINE], cwd=ROOT, capture_output=True, check=True)
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode='r:') as archive:
        for entry in archive:
            path = Path(entry.name)
            if path.is_absolute() or '..' in path.parts or not (entry.isdir() or entry.isfile()):
                raise ValueError('Unsafe baseline archive member')
            dest = destination / path
            if entry.isdir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(entry) as source, dest.open('wb') as target:
                    shutil.copyfileobj(source, target)


def _install_legacy(workspace: Path, scratch: Path, env):
    snapshot = scratch / 'legacy-source'
    snapshot.mkdir()
    _safe_archive(snapshot)
    source = """import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.framework import payload
files, block, _, _ = payload(Path(sys.argv[1]))
root=Path(sys.argv[2])
for relative, content in files.items():
    path=root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
(root/'AGENTS.md').write_bytes(block)
"""
    proc = subprocess.run([sys.executable, '-I', '-c', source, str(snapshot), str(workspace)],
                          cwd=scratch, env=env, capture_output=True, timeout=30)
    if proc.returncode:
        raise RuntimeError('Could not prepare pinned CDF 0.6 payload: ' + proc.stderr.decode(errors='replace'))


def _install_v2(workspace: Path, env):
    # Exercise the actual offline installer against a disposable fixture only.
    command = [sys.executable, '-B', str(ROOT / 'scripts/cdf.py'), 'install',
               '--target', str(workspace), '--scope', 'project', '--json']
    proc = subprocess.run(command, cwd=workspace, env=env, capture_output=True, timeout=30)
    if proc.returncode:
        raise RuntimeError('Could not install CDF 2.0 into fixture: ' + proc.stderr.decode(errors='replace'))
    try: result = json.loads(proc.stdout)
    except ValueError as exc: raise RuntimeError('Invalid CDF 2.0 installer output') from exc
    if result.get('state') == 'error': raise RuntimeError('CDF 2.0 installer reported an error')


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
    if not any(isinstance(e, dict) and e.get('type') == 'turn.completed' for e in events): return None
    observed = [e for e in events if isinstance(e, dict) and e.get('type') == 'item.completed'
                and isinstance(e.get('item'), dict) and e['item'].get('type') == 'command_execution']
    return len(observed) if observed else None


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


def _git_identity(workspace, env):
    values = []
    for args in (('rev-parse', 'HEAD'), ('symbolic-ref', '-q', 'HEAD'), ('diff', '--cached', '--binary')):
        result = subprocess.run(['git', *args], cwd=workspace, env=env, capture_output=True, timeout=15)
        values.append((result.returncode, result.stdout))
    return values


def _prepare_git_fixture(workspace, env, case_id):
    """Create the same deterministic fixture commit in each temporary condition."""
    notes = workspace / 'notes.txt'
    dirty = notes.read_bytes() if case_id == 'G14' else None
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
    cases = [case for case in data['cases'] + activations.get('executable_cases', []) if case['id'] == case_id]
    if len(cases) != 1: raise ValueError(f'Unknown or duplicate case: {case_id}')
    return cases[0]


def rubric_names(case, condition):
    """Return common behavior and CDF 2 activation assertions separately."""
    names = case['must'] + case['must_not']
    behavior = [name for name in names if not name.startswith('activate:')]
    activation = [name for name in names if name.startswith('activate:')] if condition == 'CDF_20' else []
    return behavior, activation


def scored_status(checks, *, applicable=True):
    if not applicable: return 'NOT_APPLICABLE'
    if any(c['status'] == 'FAIL' for c in checks): return 'FAIL'
    if not checks or any(c['status'] != 'PASS' for c in checks): return 'NOT_OBSERVED'
    return 'PASS'


def _case_hash(case):
    return hashlib.sha256(json.dumps(case, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def preflight(case_id, conditions, adapter, kind, protocol='prompt-v1', declared_capabilities=None):
    case = load_case(case_id)
    if not set(conditions) <= set(CONDITIONS) or not conditions: raise ValueError('Invalid conditions')
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
    answers = case.get('scripted_answers', [])
    if not isinstance(answers, list) or any(not isinstance(answer, str) for answer in answers):
        raise ValueError('Scripted answers must be a list of strings')
    controls = case.get('runtime_controls', {})
    prelude = case.get('prelude_messages', [])
    if not isinstance(controls, dict) or not isinstance(prelude, list):
        raise ValueError('Invalid scenario runtime controls or prelude')
    if any(name not in ('reviewer_available', 'force_compaction_before_prompt', 'budget_interrupt', 'deny_workspace_writes',
                           'two_workers_available', 'inject_child_decision', 'inject_child_out_of_scope_edit',
                           'change_mcp_index', 'inject_failed_repair_history') or type(value) is not bool
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
    if 'CDF_20' in conditions:
        if not (ROOT / 'scripts' / 'cdf.py').is_file(): raise ValueError('Missing CDF 2.0 installer')
        for name in CORE:
            if not (ROOT / 'skills' / name / 'SKILL.md').is_file():
                raise ValueError(f'Missing CDF 2.0 skill: {name}')
        for name in ('AGENTS.cdf-block.md', 'cdf_reviewer.toml', 'cdf_diagnostician.toml'):
            if not (ROOT / 'templates' / name).is_file(): raise ValueError(f'Missing template: {name}')
        if not (ROOT / 'subskills.catalog.json').is_file(): raise ValueError('Missing subskill catalog')
    if 'CDF_06' in conditions:
        proc = subprocess.run(['git', 'cat-file', '-e', BASELINE + '^{commit}'], cwd=ROOT, capture_output=True)
        if proc.returncode: raise ValueError('Pinned CDF 0.6 source commit unavailable')
    return {'case_id': case_id, 'conditions': conditions, 'fixture_revision': case['fixture_revision'],
            'adapter': str(adapter), 'adapter_kind': kind, 'adapter_protocol': protocol,
            'scripted_answer_count': len(answers), 'runtime_controls': controls,
            'dialogue_capability': ('operator_asserted_unverified' if protocol == 'json-dialogue-v1' else
                                    'native_resume_unverified' if kind == 'codex' and answers else 'unsupported'),
            'runtime_version': _runtime_version(adapter, kind), 'model_observed': None,
            'capabilities': 'unverified', 'limitations': [
                'Adapter executable and generated fixture code require an external OS sandbox.',
                'Model, sandbox, agent availability, skill loads and comparable usage are not inferred.',
                'No user credentials are supplied; Codex authentication may be unavailable.',
                'External dialogue support is operator-asserted; actual answer delivery is not verified.',
                'Native resume requires an observed session ID and question; compaction and reviewer controls require an external adapter.',
                'Automated trace grading is not implemented.']}


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
        state,code,out,err,duration = _process(command,workspace,home_env,answer,timeout)
        outputs.append((out,err)); elapsed += duration
        stdout += (b'\n' if stdout and not stdout.endswith(b'\n') else b'') + out
        stderr += (b'\n' if stderr and not stderr.endswith(b'\n') else b'') + err
        if state != 'completed' or code != 0: return (state,code,stdout,stderr,elapsed), outputs
        # A resumed turn need not emit thread.started; only its question matters.
        _, question = _native_thread_and_question(out)
    return (state,code,stdout,stderr,elapsed), outputs


def run_one(case, condition, output, adapter, kind, seed, timeout, model=None, effort=None, runtime_version='unverified', protocol='prompt-v1', declared_capabilities=None):
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
        if condition == 'CDF_06': _install_legacy(workspace, scratch, env)
        elif condition == 'CDF_20': _install_v2(workspace, env)
        before = _snapshot(workspace, skip_git=True)
        guidance = {path: value for path, value in before.items() if path not in fixture_initial}
        guidance_hash = _hash_snapshot(guidance)
        git_initial = _git_identity(workspace, env)
        _save(folder / 'prompt.txt', case['prompt'] + '\n')
        _save(folder / 'initial_sha.txt', git_head + '\n')
        _json(folder / 'workspace-before.json', _snapshot_metadata(before))
        _json(folder / 'environment.json', {'condition': condition, 'fixture_revision': case['fixture_revision'],
              'fixture_sha256': fixture_hash, 'case_sha256': _case_hash(case),
              'fixture_git_head': git_head,
              'cdf_06_source': BASELINE if condition == 'CDF_06' else None,
              'guidance_sha256': guidance_hash, 'home_isolated': True, 'credentials_inherited': False,
              'runtime_version': runtime_version, 'model_requested': model, 'model_observed': None,
              'effort_requested': effort, 'effort_observed': None,
              'adapter_kind': kind, 'adapter_protocol': protocol,
              'requested_runtime_controls': case.get('runtime_controls', {}),
              'declared_adapter_capabilities': declared_capabilities,
              'dialogue_capability': ('operator_asserted_unverified' if protocol == 'json-dialogue-v1' else
                                      'native_resume_unverified' if kind == 'codex' and case.get('scripted_answers') else 'unsupported'),
              'agent_availability': 'unverified', 'skill_discovery': 'unverified',
              'codebase_memory': 'not_installed_or_probed',
              'parity_limitations': ['CDF 0.6 declares Codebase Memory but this runner does not install or activate it.',
                                     'Runtime model, tools and agent discovery are not verified.'],
              'os_sandbox': 'external adapter responsibility', 'usage_measurement': 'see_run_record'})
        command = [str(adapter)]
        if kind == 'codex':
            command += ['exec', '--json']
            if not case.get('scripted_answers'): command += ['--ephemeral']
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
        if before_answers is not None:
            checks.append({'name':'workspace_unchanged_before_answers',
                           'status':'PASS' if before_answers == before else 'FAIL',
                           'evidence':'Compared workspace snapshot before supplying scripted answers.'})
        if case['no_fixture_edits']:
            ok = before == after
            checks.append({'name': 'fixture_source_unchanged', 'status': 'PASS' if ok else 'FAIL',
                           'evidence': 'Compared all workspace paths, file types, contents and permission modes.'})
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
        return record


def run(case_id, conditions, adapter, kind, output, seed=0, timeout=300, model=None, effort=None, protocol='prompt-v1', declared_capabilities=None):
    capabilities = preflight(case_id, conditions, adapter, kind, protocol, declared_capabilities)
    case = load_case(case_id)
    output.mkdir(parents=True, exist_ok=False)
    order = list(conditions); random.Random(seed).shuffle(order)
    _json(output / 'manifest.json', {'case_id': case_id, 'seed': seed, 'conditions': order,
                                    'baseline': BASELINE, 'status': 'planned'})
    records = []
    for condition in order:
        try:
            records.append(run_one(case, condition, output, adapter, kind, seed, timeout, model, effort,
                                   capabilities['runtime_version'], protocol, declared_capabilities))
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            folder = output / condition
            folder.mkdir(exist_ok=True)
            # Preserve any artifacts written before preparation or checking failed.
            if not (folder / 'stdout.ndjson').exists(): _save(folder / 'stdout.ndjson', '')
            if not (folder / 'stderr.txt').exists(): _save(folder / 'stderr.txt', str(exc))
            behavior_names, activation_names = rubric_names(case, condition)
            checks = [{'name': n, 'status': 'NOT_OBSERVED', 'evidence': 'Runner failed.'}
                      for n in behavior_names]
            activation_checks = [{'name': n, 'status': 'NOT_OBSERVED', 'evidence': 'Runner failed.'}
                                 for n in activation_names]
            record = {'schema': 2, 'rubric_version': RUBRIC_VERSION, 'activation_result': 'RUNNER_ERROR',
                      'activation_checks': activation_checks, 'case_id': case_id, 'condition': condition, 'seed': seed,
                      'runtime_version': 'unverified', 'model_requested': model, 'model_observed': None,
                      'result': 'RUNNER_ERROR', 'acceptance_checks': checks,
                      'resource_measurement': {'basis': 'not_available', 'input_tokens': None,
                                               'output_tokens': None, 'elapsed_seconds': None},
                      'raw_trace_path': 'stdout.ndjson'}
            validate_record('eval-run', record)
            if not (folder / 'run.json').exists(): _json(folder / 'run.json', record)
            if not (folder / 'failure-notes.md').exists():
                _save(folder / 'failure-notes.md', f'Runner failed: {exc}\n')
            records.append(record)
    _json(output / 'results.json', records)
    return records
