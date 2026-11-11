#!/usr/bin/env python3
"""Probe CDF discovery in a temporary home via app-server; never run a model."""
import argparse
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cdf_installer import core


def probe(binary):
    with tempfile.TemporaryDirectory(prefix='cdf-discovery-') as temporary:
        base = Path(temporary).resolve()
        home = base / 'home'
        (home / '.codex').mkdir(parents=True)
        target = base / 'project'
        target.mkdir()
        env = {'HOME': str(home), 'CODEX_HOME': str(home / '.codex'),
               'PATH': os.environ.get('PATH', ''), 'TMPDIR': str(base)}
        with patch.object(Path, 'home', return_value=home), patch.dict(os.environ, {'CODEX_HOME': env['CODEX_HOME']}):
            core.perform(target, 'project', 'install', enable=('learning', 'operator'))
        with (base / 'stderr.log').open('w+b') as errors:
            process = subprocess.Popen([str(binary), 'app-server', '--listen', 'stdio://'],
                                       cwd=target, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=errors)
            pending = b''

            def send(message):
                process.stdin.write((json.dumps(message) + '\n').encode())
                process.stdin.flush()

            def receive(request_id):
                nonlocal pending
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if b'\n' in pending:
                        line, pending = pending.split(b'\n', 1)
                        message = json.loads(line)
                        if message.get('id') == request_id:
                            if 'error' in message:
                                raise ValueError(str(message['error']))
                            return message['result']
                        continue
                    if select.select([process.stdout], [], [], max(0, deadline - time.monotonic()))[0]:
                        data = os.read(process.stdout.fileno(), 65536)
                        if not data:
                            errors.seek(0)
                            raise ValueError('App-server exited: ' + errors.read(2000).decode(errors='replace'))
                        pending += data
                raise ValueError('App-server request timed out')

            try:
                send({'id': 1, 'method': 'initialize', 'params': {
                    'clientInfo': {'name': 'cdf_discovery_probe', 'version': '1.0.0'},
                    'capabilities': {'experimentalApi': True}}})
                initialized = receive(1)
                send({'method': 'initialized', 'params': {}})
                send({'id': 2, 'method': 'skills/list', 'params': {
                    'cwds': [str(target)], 'forceReload': True}})
                rows = receive(2)['data']
                skills = [skill for row in rows for skill in row['skills']
                          if skill['name'] == 'cdf' or skill['name'].startswith('cdf-')]
                local_errors = [error for row in rows for error in row.get('errors', [])]
                if [skill['name'] for skill in skills] != ['cdf'] or local_errors:
                    raise ValueError('Unexpected discovery entries or errors')
                skill = skills[0]
                interface = skill.get('interface') or {}
                if not skill.get('enabled') or not all(
                    Path(interface.get(key, '')).is_file() for key in ('iconSmall', 'iconLarge')
                ):
                    raise ValueError('CDF is disabled or its icon paths are unavailable')
                return {'state': 'passed', 'probe': 'skills/list', 'cdf_entries': ['cdf'],
                        'enabled': True, 'small_icon': Path(interface['iconSmall']).suffix,
                        'large_icon': Path(interface['iconLarge']).suffix, 'errors': [],
                        'model_runs': 0, 'home': 'temporary', 'client': initialized.get('userAgent')}
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                process.stdin.close()
                process.stdout.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex', type=Path, required=True, help='Path to a Codex executable supporting app-server')
    args = parser.parse_args()
    try:
        result = probe(args.codex.expanduser().resolve())
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({'state': 'unavailable', 'message': str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
