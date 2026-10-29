"""Installer availability checks never start model turns."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('cdf_availability', Path(__file__).resolve().parents[1]/'scripts/framework.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.target = Path(self.tmp.name).resolve()
        self.name = '.agents/skills/code-delivery-framework/delivery/SKILL.md'
        self.path = self.target/self.name
        self.path.parent.mkdir(parents=True)
        self.path.write_text('skill')
        self.health = {'state':'installed', 'files':{self.name:'clean'}}

    def check(self, response, global_mode=False):
        with patch.object(f, 'status', return_value=self.health), patch.object(f, 'probe', return_value=response) as probe:
            result = f.installation_availability('codex', self.target, self.target, global_mode)
            self.assertEqual(probe.call_args.kwargs['skill_cwd'], self.target)
            if global_mode:
                self.assertEqual(probe.call_args.kwargs['env']['HOME'], str(self.target))
            return result

    def test_enabled_exact_path_is_verified(self):
        result = self.check({'data':[{'cwd':str(self.target),'skills':[{'path':str(self.path),'enabled':True}],'errors':[]}]})
        self.assertEqual(result['files'], 'verified')
        self.assertEqual(result['skills']['state'], 'verified')
        self.assertIn('active session unverified', result['mcp'])

    def test_disabled_or_other_path_is_not_discovered(self):
        for skill in ({'path':str(self.path),'enabled':False}, {'path':'/other/SKILL.md','enabled':True}):
            result = self.check({'data':[{'cwd':str(self.target),'skills':[skill],'errors':[]}]})
            self.assertEqual(result['skills']['state'], 'incomplete')
            self.assertEqual(result['skills']['missing'], [self.name])

    def test_global_discovery_uses_requested_home(self):
        self.check({'data':[{'cwd':str(self.target),'skills':[]}]}, True)

    def test_runtime_failure_is_unverified_without_undoing_install(self):
        with patch.object(f, 'status', return_value=self.health), patch.object(f, 'probe', side_effect=f.FrameworkError('unsupported')):
            result = f.installation_availability('codex', self.target, self.target)
        self.assertEqual(result['skills']['state'], 'unverified')
        self.assertTrue(self.path.is_file())

    def test_modified_bytes_are_reported_separately(self):
        self.health['files'][self.name] = 'modified'
        result = self.check({'data':[{'cwd':str(self.target),'skills':[]}]})
        self.assertEqual(result['files'], 'incomplete')


if __name__ == '__main__': unittest.main()
