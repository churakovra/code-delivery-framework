"""Prerequisite and execution opt-in checks, without real model execution."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from evals.compatibility import inspect_case
from evals import runner

ROOT = Path(__file__).resolve().parents[1]


class CompatibilityTests(unittest.TestCase):
    def test_missing_prerequisites_stop_before_execution_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'unavailable'
            report = {'status': 'UNAVAILABLE', 'missing_prerequisites': ['node']}
            with patch('evals.runner.inspect_case', return_value=report), \
                    patch('evals.runner._process') as process:
                with self.assertRaisesRegex(ValueError, 'Evaluation unavailable: node'):
                    runner.run('G08', ['BASE'], Path(sys.executable), 'external', output,
                               trusted_local_execution=True)
            process.assert_not_called()
            self.assertFalse(output.exists())

    def test_missing_node_is_unavailable_not_a_behavioral_failure(self):
        report = inspect_case({'id': 'G08'}, 'external', platform_name='posix',
                              find_executable=lambda name: None if name == 'node' else '/bin/git')
        self.assertEqual(report['status'], 'UNAVAILABLE')
        self.assertEqual(report['missing_prerequisites'], ['node'])

    def test_non_posix_is_explicitly_unavailable(self):
        report = inspect_case({'id': 'G01'}, 'external', platform_name='nt',
                              find_executable=lambda name: '/bin/' + name)
        self.assertEqual(report['status'], 'UNAVAILABLE')
        self.assertIn('POSIX', report['missing_prerequisites'][0])

    def test_resume_and_controls_are_requirements_not_verified_capabilities(self):
        report = inspect_case({'id': 'G19', 'scripted_answers': ['yes'],
                               'runtime_controls': {'reviewer_available': True}}, 'codex',
                              platform_name='posix', find_executable=lambda name: '/bin/' + name)
        self.assertTrue(report['native_resume_required'])
        self.assertEqual(report['required_runtime_controls'], ['reviewer_available'])
        self.assertEqual(report['runtime_version_validation'], 'UNVERIFIED')

    def test_cli_refuses_untrusted_execution_before_adapter_or_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            sentinel = folder / 'ran'
            adapter = folder / 'adapter'
            adapter.write_text('#!' + sys.executable + '\nfrom pathlib import Path\n'
                               f'Path({str(sentinel)!r}).touch()\n')
            adapter.chmod(0o755)
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/run_cdf_evaluation.py'),
                                     '--case', 'G01', '--adapter', str(adapter),
                                     '--adapter-kind', 'codex', '--allow-model-runs',
                                     '--output', str(folder / 'results')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('trusted-local-execution', result.stderr)
            self.assertFalse(sentinel.exists())
            self.assertFalse((folder / 'results').exists())

    def test_codex_preflight_does_not_execute_version_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            sentinel = folder / 'ran'
            adapter = folder / 'adapter'
            adapter.write_text('#!' + sys.executable + '\nfrom pathlib import Path\n'
                               f'Path({str(sentinel)!r}).touch()\n')
            adapter.chmod(0o755)
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/run_cdf_evaluation.py'),
                                     '--case', 'G01', '--adapter', str(adapter),
                                     '--adapter-kind', 'codex', '--preflight'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['runtime_version'], 'unverified')
            self.assertFalse(sentinel.exists())
