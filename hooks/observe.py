"""Opt-in desktop metadata observer. No source/transcript reads or model calls."""
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

LIMIT = 1024 * 1024
EVENTS = ('SessionStart', 'SubagentStart', 'SubagentStop')


def _metadata(path):
    """Read only a known CDF metadata file, never source or transcripts."""
    try:
        if any(p.is_symlink() for p in (path, *path.parents)): return {}
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 65536: return {}
            data = json.loads(stream.read(65537))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def session_context(payload):
    """Detection only: configured role files do not establish availability/routing."""
    root = Path(__file__).resolve().parents[1]
    manifest = _metadata(root / '.codex-plugin/plugin.json')
    version = manifest.get('version')
    if not isinstance(version, str) or not re.fullmatch(r'[0-9A-Za-z.+-]{1,64}', version):
        version = 'unknown'
    roots = []
    cwd = payload.get('cwd')
    if isinstance(cwd, str) and Path(cwd).is_absolute(): roots.append(Path(cwd))
    roots.append(Path.home())
    profile = 'unknown'
    role_files = 'not_detected'
    for base in roots:
        receipt = _metadata(base / '.codex/cdf/backups/native-agents.json')
        if receipt.get('schema') == 1 and receipt.get('profile') in ('budget', 'balanced', 'quality'):
            profile = receipt['profile']
            role_files = 'detected' if all((base / '.codex/agents' / (role + '.toml')).is_file()
                         for role in ('cdf_explorer', 'cdf_reviewer', 'cdf_diagnostician')) else 'incomplete'
            break
    return {'bundle_version_detected': version, 'profile_configured': profile,
            'mode': 'desktop-controlled', 'hook_execution': 'OBSERVED',
            'role_files': role_files, 'agent_availability': 'NOT_CHECKED',
            'routing': 'NOT_OBSERVED', 'skill_application': 'NOT_OBSERVED'}


def observe(payload, data_path):
    if not isinstance(payload, dict) or payload.get('hook_event_name') not in EVENTS:
        raise ValueError('Unsupported event')
    row = {'schema': 1, 'source': 'observed_hook', 'event': payload['hook_event_name'],
           'time': time.time(), 'status': 'OBSERVED', 'effort_observed': None}
    for source, target in (('session_id', 'session_id'), ('agent_id', 'agent_id'),
                           ('agent_type', 'role'), ('model', 'model_observed')):
        value = payload.get(source)
        if value is not None and (not isinstance(value, str) or not re.fullmatch(r'[\w.:/-]{1,256}', value, re.ASCII)):
            raise ValueError('Invalid metadata')
        row[target] = value
    if not row['session_id']:
        raise ValueError('Missing session id')
    if row['event'] == 'SessionStart':
        row['context'] = session_context(payload)
    # PLUGIN_DATA is supplied by the host. Never choose a path from hook input.
    data_path = Path(data_path)
    if not data_path.is_absolute():
        raise ValueError('Absolute host data path required')
    data_path.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory = os.open(data_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fd = os.open('events.jsonl', os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                     0o600, dir_fd=directory)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size >= LIMIT:
                raise ValueError('Unsafe or full event log')
            os.fchmod(fd, 0o600)
            os.write(fd, (json.dumps(row, separators=(',', ':')) + '\n').encode())
        finally:
            os.close(fd)
    finally:
        os.close(directory)
    return row


def main():
    try:
        raw = sys.stdin.buffer.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError('Oversized input')
        row = observe(json.loads(raw), os.environ['PLUGIN_DATA'])
        if row['event'] == 'SessionStart':
            context = row['context']
            text = ('CDF ' + context['bundle_version_detected'] + '; mode=desktop-controlled; profile='
                    + context['profile_configured'] + '; role files=' + context['role_files']
                    + '. SessionStart observed. Agent availability, routing and skill application are not verified.')
            print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': text}}))
        else:
            print('{}')
    except (ValueError, OSError, KeyError, TypeError):
        # Diagnostic only: never deny a tool, inject raw input or continue a turn.
        print(json.dumps({'systemMessage': 'CDF observation degraded: event was not recorded.'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
