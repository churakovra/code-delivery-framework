"""Independent outcome oracles reject green but irrelevant fixture tests."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class OutcomeFixtureTests(unittest.TestCase):
    def test_oracles_reject_original_and_accept_targeted_repair(self):
        for name in ('G28', 'G29', 'G31'):
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temp:
                workspace = Path(temp) / 'fixture'
                shutil.copytree(ROOT / 'evals/fixtures' / name, workspace)
                script = 'import runpy,sys;sys.path.insert(0,".");runpy.run_path(sys.argv[1],run_name="__main__")'
                command = [sys.executable, "-I", "-c", script, str(ROOT / "evals/checks" / (name + ".py"))]
                self.assertNotEqual(subprocess.run(command, cwd=workspace, capture_output=True).returncode, 0)
                app = workspace / 'app.py'
                app.write_text(app.read_text().replace('return "old"', 'return "hello"'))
                self.assertEqual(subprocess.run(command, cwd=workspace, capture_output=True).returncode, 0)
                if name != 'G31':
                    app.write_text(app.read_text().replace('spacing = 12', 'spacing = 99'))
                    self.assertNotEqual(subprocess.run(command, cwd=workspace, capture_output=True).returncode, 0)
                    observation = ROOT / "evals/checks" / (name + "-observation.py")
                    self.assertEqual(subprocess.run([sys.executable, str(observation), str(workspace)], capture_output=True).returncode, 0)

    def test_review_case_is_read_only_and_not_automatically_scored(self):
        cases = json.loads((ROOT / 'evals/golden-cases.json').read_text())['cases']
        case = next(case for case in cases if case['id'] == 'G30')
        self.assertTrue(case['no_fixture_edits'])
        self.assertIsNone(case['deterministic_check'])
