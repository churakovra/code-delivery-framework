#!/usr/bin/env python3
"""Run the bounded counter evaluation with an explicitly supplied agent adapter.

Adapter contract: executable path; cwd is the isolated project; prompt on stdin;
stdout/stderr are captured unedited; exit zero means the task process completed.
The adapter must isolate its own runtime configuration and credentials.
"""
import argparse
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'evaluation-cases/simple-counter-change.json'


def run(runner, output, seed, timeout):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    case = json.loads(CASE.read_text())
    order = ['baseline', 'framework']
    random.Random(seed).shuffle(order)
    result = {'case': case['id'], 'seed': seed, 'order': order,
              'runner': str(runner), 'conditions': {},
              'limitations': ['Adapter runtime isolation and model identity are supplied by the operator.',
                              'One run per condition is not a statistical comparison.',
                              'Behavioral check does not score instruction following or code quality.']}
    for condition in order:
        folder = output / condition
        folder.mkdir()
        with tempfile.TemporaryDirectory(prefix='cdf-eval-') as scratch:
            workspace = Path(scratch) / 'project'
            workspace.mkdir()
            for name, content in case['files'].items():
                (workspace / name).write_text(content)
            if condition == 'framework':
                try:
                    from .framework import payload
                except ImportError:
                    from framework import payload
                files, block, _, _ = payload(ROOT)
                for name, content in files.items():
                    target = workspace / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                (workspace / 'AGENTS.md').write_bytes(block)
            started = time.monotonic()
            try:
                proc = subprocess.run([str(runner)], cwd=workspace, input=case['prompt'],
                                      text=True, capture_output=True, timeout=timeout)
                exit_code, stdout, stderr, state = proc.returncode, proc.stdout, proc.stderr, 'completed'
            except subprocess.TimeoutExpired as exc:
                exit_code, state = None, 'timeout'
                stdout = exc.stdout or b''
                stderr = exc.stderr or b''
                stdout = stdout.decode(errors='replace') if isinstance(stdout, bytes) else stdout
                stderr = stderr.decode(errors='replace') if isinstance(stderr, bytes) else stderr
            except OSError as exc:
                exit_code, stdout, stderr, state = None, '', str(exc), 'runner-error'
            (folder / 'stdout.txt').write_text(stdout)
            (folder / 'stderr.txt').write_text(stderr)
            # Preserve the actual workspace before running any verification.
            shutil.copytree(workspace, folder / 'workspace', symlinks=True)
            check = None
            if state == 'completed' and exit_code == 0:
                code = ('import app; assert app.activate("x") is True; '
                        'assert app.count == 1; assert app.activate("") is False; '
                        'assert app.count == 1')
                try:
                    checked = subprocess.run([sys.executable, '-c', code], cwd=workspace,
                                             text=True, capture_output=True, timeout=30)
                    check_out, check_err, check_exit = checked.stdout, checked.stderr, checked.returncode
                    check_state = 'completed'
                except subprocess.TimeoutExpired as exc:
                    check_out, check_err, check_exit, check_state = '', str(exc), None, 'timeout'
                except OSError as exc:
                    check_out, check_err, check_exit, check_state = '', str(exc), None, 'error'
                (folder / 'check.stdout.txt').write_text(check_out)
                (folder / 'check.stderr.txt').write_text(check_err)
                check = {'state': check_state, 'exit_code': check_exit,
                         'command': 'python -c <counter behavior assertion>'}
            result['conditions'][condition] = {'state': state, 'runner_exit_code': exit_code,
                                               'duration_seconds': round(time.monotonic() - started, 3),
                                               'behavior_check': check}
            (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runner', type=Path, required=True, help='Executable agent adapter; no shell expansion')
    parser.add_argument('--output', type=Path, required=True, help='New directory for traces and snapshots')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error('--timeout must be positive')
    runner = args.runner.resolve()
    if not runner.is_file() or not os.access(runner, os.X_OK):
        parser.error('runner must be an executable file')
    try:
        result = run(runner, args.output, args.seed, args.timeout)
    except FileExistsError:
        parser.error('output directory already exists')
    print(json.dumps(result, indent=2))
    return 0 if all(c['state'] == 'completed' and c['runner_exit_code'] == 0 and c['behavior_check']['exit_code'] == 0 for c in result['conditions'].values()) else 1

if __name__ == '__main__':
    raise SystemExit(main())
