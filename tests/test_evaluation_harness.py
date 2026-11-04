"""Exercise harness mechanics; these are not model evaluations."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / 'scripts/run_evaluation.py'


class EvaluationHarnessTests(unittest.TestCase):
    def test_runs_both_conditions_and_captures_real_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            adapter = tmp / 'adapter'
            adapter.write_text('#!/usr/bin/env python3\nfrom pathlib import Path\nimport sys\n'
                               'sys.stdin.read()\nPath("app.py").write_text('
                               '"count = 0\\ndef activate(code):\\n    global count\\n    if code: count += 1\\n    return bool(code)\\n")\n')
            adapter.chmod(0o755)
            output = tmp / 'result'
            run = subprocess.run([sys.executable, str(HARNESS), '--runner', str(adapter),
                                  '--output', str(output), '--seed', '4'], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads((output/'result.json').read_text())
            self.assertEqual(set(report['conditions']), {'baseline', 'framework'})
            self.assertEqual(report['conditions']['baseline']['behavior_check']['exit_code'], 0)
            self.assertTrue((output/'framework/workspace/AGENTS.md').is_file())
            self.assertFalse((output/'baseline/workspace/AGENTS.md').exists())
            self.assertTrue((output/'framework/workspace/.agents/skills/code-delivery-framework/delivery/SKILL.md').is_file())

    def test_failed_runner_is_not_scored_as_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            adapter = tmp/'adapter'
            adapter.write_text('#!/bin/sh\necho failed >&2\nexit 7\n')
            adapter.chmod(0o755)
            output = tmp/'result'
            run = subprocess.run([sys.executable, str(HARNESS), '--runner', str(adapter), '--output', str(output)], capture_output=True)
            self.assertEqual(run.returncode, 1)
            report = json.loads((output/'result.json').read_text())
            for condition in report['conditions'].values():
                self.assertEqual(condition['runner_exit_code'], 7)
                self.assertIsNone(condition['behavior_check'])

    def test_timed_out_check_is_recorded_not_lost(self):
        from scripts import run_evaluation
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'result'
            def fake_run(command, **kwargs):
                if command[0] == sys.executable:
                    raise subprocess.TimeoutExpired(command, 30)
                return subprocess.CompletedProcess(command, 0, stdout='trace', stderr='')
            with mock.patch.object(run_evaluation.subprocess, 'run', side_effect=fake_run):
                report = run_evaluation.run(Path('/adapter'), output, 0, 30)
            self.assertTrue((output / 'result.json').exists())
            for condition in report['conditions'].values():
                self.assertEqual(condition['behavior_check']['state'], 'timeout')
                self.assertIsNone(condition['behavior_check']['exit_code'])

if __name__ == '__main__':
    unittest.main()
