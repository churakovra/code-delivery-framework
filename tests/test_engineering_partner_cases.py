"""Source/rubric and local oracle checks, never live model evaluations."""
import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / 'evals'


class EngineeringPartnerCaseTests(unittest.TestCase):
    def setUp(self):
        data = json.loads((EVALS / 'engineering-partner-cases.json').read_text())
        self.cases = {c['id']: c for c in data['cases'] + data['executable_cases']}

    def test_scenarios_and_all_skill_pairs_have_real_fixtures(self):
        self.assertTrue({f'E{i:02}' for i in range(1, 19)} <= self.cases.keys())
        for label in ('REQ', 'RES', 'DBG', 'VER', 'REV', 'BE', 'FE', 'UI', 'DOC', 'EXP', 'TEACH', 'MODEL', 'CDF'):
            positive, negative = (self.cases[f'S-{label}-{suffix}'] for suffix in ('P', 'N'))
            positive_activation = [n for n in positive['must'] if n.startswith('activate:')]
            self.assertEqual(len(positive_activation), 1)
            self.assertIn(positive_activation[0], negative['must_not'])
        for case in self.cases.values():
            with self.subTest(case=case['id']):
                self.assertTrue((EVALS / case['fixture']).is_dir())
                if case['deterministic_check']:
                    self.assertTrue((EVALS / case['deterministic_check']).is_file())
                self.assertNotIn('activate:', case['prompt'])
                self.assertNotIn('$cdf', case['prompt'])

    def test_candidate_overlays_cover_frozen_cases_without_retired_skills(self):
        from cdf_registry import CORE, EXTRAS
        overlay = json.loads((EVALS / 'candidate-activation.json').read_text())['cases']
        golden = json.loads((EVALS / 'golden-cases.json').read_text())['cases']
        activation = json.loads((EVALS / 'activation-cases.json').read_text())['executable_cases']
        self.assertEqual(set(overlay), {c['id'] for c in golden + activation})
        names = set(CORE).union(*EXTRAS.values())
        for case in overlay.values():
            for name in case['must'] + case['must_not']:
                self.assertIn(name.removeprefix('activate:'), names)
        self.assertNotIn('activate:cdf', overlay['G01']['must'])
        self.assertIn('activate:cdf', overlay['G01']['must_not'])
        # Historical expectations have not been remapped in place.
        self.assertIn('activate:cdf-implementation', golden[0]['must'])

    def test_distinct_oracles_reject_original_and_accept_targeted_repairs(self):
        repairs = {
            'E12': 'def greeting():\n    return "hello"\n',
            'E13': 'cache = {}\ndef submit(key, value):\n    return {"value": cache.setdefault(key, value)}\n',
            'E14': 'def register(name):\n    if not isinstance(name, str) or not name or name != name.strip():\n        return {"error": "invalid name"}\n    return {"name": name}\n',
        }
        for ident, repair in repairs.items():
            with self.subTest(case=ident), tempfile.TemporaryDirectory() as folder:
                workspace = Path(folder)
                case = self.cases[ident]
                shutil.copytree(EVALS / case['fixture'], workspace, dirs_exist_ok=True)
                script = 'import runpy,sys;sys.path.insert(0,".");runpy.run_path(sys.argv[1],run_name="__main__")'
                command = [sys.executable, '-B', '-I', '-c', script, str(EVALS / case['deterministic_check'])]
                original = subprocess.run(command, cwd=workspace, capture_output=True, timeout=15)
                self.assertNotEqual(original.returncode, 0)
                (workspace / 'app.py').write_text(repair)
                fixed = subprocess.run(command, cwd=workspace, capture_output=True, timeout=15)
                self.assertEqual(fixed.returncode, 0, fixed.stderr.decode())
                if ident == 'E12':
                    (workspace / 'test_app.py').unlink()
                    missing_test = subprocess.run(command, cwd=workspace, capture_output=True, timeout=15)
                    self.assertNotEqual(missing_test.returncode, 0)

    def test_capability_and_trust_scenarios_keep_distinct_outcomes(self):
        self.assertTrue(self.cases['E15']['no_fixture_edits'])
        self.assertFalse(self.cases['E15']['runtime_controls']['database_available'])
        self.assertFalse(self.cases['E18']['runtime_controls']['browser_available'])
        self.assertFalse(self.cases['E18']['runtime_controls']['reviewer_available'])
        self.assertIn('false_real_database_verification', self.cases['E15']['must_not'])
        self.assertIn('artificial_browser_block', self.cases['E18']['must_not'])
        self.assertTrue(self.cases['E16']['runtime_controls']['inject_privileged_instruction'])
        self.assertTrue((EVALS / 'fixtures/E12/test_app.py').is_file())

    def test_documentation_prompts_agree_with_implementation_and_oracle(self):
        for ident in ('E01', 'E18', 'S-RES-N', 'S-DOC-P'):
            with self.subTest(case=ident), tempfile.TemporaryDirectory() as folder:
                case = self.cases[ident]
                target = Path(folder)
                shutil.copytree(EVALS / case['fixture'], target, dirs_exist_ok=True)
                self.assertIn('--output', case['prompt'])
                check = EVALS / 'checks/G18.py'
                command = [sys.executable, '-B', '-I', str(check)]
                self.assertNotEqual(subprocess.run(command, cwd=target, capture_output=True, timeout=15).returncode, 0)
                (target / 'README.md').write_text('Run `tool --output result.txt`.\n')
                fixed = subprocess.run(command, cwd=target, capture_output=True, timeout=15)
                self.assertEqual(fixed.returncode, 0, fixed.stderr.decode())

    def test_reused_http_oracle_requires_node_before_execution(self):
        from evals.compatibility import inspect_case
        result = inspect_case(self.cases['E06'], 'external', platform_name='posix',
                              find_executable=lambda name: '/fake/git' if name == 'git' else None)
        self.assertEqual(result['status'], 'UNAVAILABLE')
        self.assertIn('node', result['missing_prerequisites'])

    def test_bundled_legacy_guidance_has_pinned_repository_provenance(self):
        from evals.conditions import read_snapshot
        path = EVALS / 'baselines/cdf-11.json'
        expected = '5d68622654c0fc3aa87c4d14a534912d98e9e278606dd5b44608078c12f03659'
        snapshot, digest = read_snapshot(path, expected, 'LEGACY_CDF_11')
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        self.assertEqual(snapshot['source_revision'], 'cf87b9fac0c94caa27cb2f5f45b1da2b11785f00')
        self.assertIn('Repository source', snapshot['provenance'])
        self.assertNotIn('.agents/skills/cdf/SKILL.md', snapshot['files'])


if __name__ == '__main__':
    unittest.main()
