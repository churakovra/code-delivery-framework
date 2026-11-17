"""Technical context/privacy/package checks; no model or behavioral evaluation."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cdf_registry import CORE
from cdf_runtime.hooks import runtime_status
from hooks.cdf_context import CONTEXTS, output_for
from hooks.observe import LIMIT, observe
from scripts.package_cdf_plugin import build_plugin


class DesktopHooks(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.payload = {'hook_event_name': 'SessionStart', 'session_id': 'parent-1',
                        'source': 'startup', 'prompt': 'SECRET', 'transcript_path': '/SECRET',
                        'tool_input': {'command': 'SECRET'}, 'model': 'SECRET'}

    @contextmanager
    def server(self, *, trusted=False, duplicate=False, unexpected=False):
        def request(method, params):
            if method == 'plugin/list':
                return {'marketplaces': [{'plugins': [{'id': 'code-delivery-framework@local',
                                                       'installed': True, 'enabled': True}]}]}
            if method == 'skills/list':
                return {'data': [{'skills': [{'name': 'code-delivery-framework:' + name, 'enabled': True}
                                             for name in CORE], 'errors': []}]}
            events = ['sessionStart', 'userPromptSubmit', 'subagentStart']
            if duplicate: events.append('sessionStart')
            if unexpected: events.append('subagentStop')
            return {'data': [{'hooks': [{'pluginId': 'code-delivery-framework@local', 'eventName': event,
                                        'enabled': True, 'trustStatus': 'trusted' if trusted else 'untrusted',
                                        'source': 'plugin'} for event in events], 'errors': [], 'warnings': []}]}
        yield request, {'userAgent': 'fake'}

    def test_three_event_json_and_allowlisted_emission_history(self):
        script = Path(__file__).resolve().parents[1] / 'hooks/cdf_context.py'
        env = {'PATH': os.environ.get('PATH', ''), 'PLUGIN_DATA': str(self.base), 'PYTHONDONTWRITEBYTECODE': '1'}
        for event in CONTEXTS:
            payload = dict(self.payload, hook_event_name=event)
            result = subprocess.run([sys.executable, '-B', str(script)], input=json.dumps(payload),
                                    capture_output=True, text=True, env=env, timeout=5)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout), output_for(payload))
            self.assertNotIn('SECRET', result.stdout)
        rows = [json.loads(line) for line in (self.base / 'events.jsonl').read_text().splitlines()]
        for row in rows:
            self.assertEqual(set(row), {'schema', 'source', 'event', 'session_id', 'time', 'status',
                                        'context_sha256', 'context_emitted'})
            self.assertEqual(row['context_sha256'], hashlib.sha256(CONTEXTS[row['event']].encode()).hexdigest())
            self.assertIs(row['context_emitted'], True)
        self.assertNotIn('SECRET', (self.base / 'events.jsonl').read_text())
        self.assertEqual((self.base / 'events.jsonl').stat().st_mode & 0o777, 0o600)

    def test_context_is_deterministic_for_every_session_source(self):
        for source in ('startup', 'resume', 'clear', 'compact', 'fork'):
            self.assertEqual(output_for(dict(self.payload, source=source)), output_for(self.payload))
        with self.assertRaises(ValueError): output_for({'hook_event_name': 'Stop'})
        self.assertIn('TEACH', CONTEXTS['SessionStart'])
        self.assertIn('cdf-testing', CONTEXTS['UserPromptSubmit'])
        self.assertLess(len(CONTEXTS['SessionStart']), 3100)
        self.assertLess(len(CONTEXTS['UserPromptSubmit']), 650)

    def test_symlink_fifo_and_full_logs_are_preserved(self):
        protected = self.base / 'protected'; protected.write_text('keep')
        log = self.base / 'events.jsonl'; log.symlink_to(protected)
        with self.assertRaises(OSError): observe(self.payload, self.base)
        self.assertEqual(protected.read_text(), 'keep')
        log.unlink(); os.mkfifo(log)
        with self.assertRaises(OSError): observe(self.payload, self.base)
        log.unlink(); log.write_bytes(b'x' * LIMIT)
        with self.assertRaises(ValueError): observe(self.payload, self.base)
        self.assertEqual(log.stat().st_size, LIMIT)

    def test_discovery_trust_emission_and_application_are_distinct(self):
        observe(self.payload, self.base, context_sha256=hashlib.sha256(CONTEXTS['SessionStart'].encode()).hexdigest())
        with patch('cdf_runtime.hooks.app_server', lambda *a, **k: self.server()):
            result = runtime_status('fake', cwd=self.base, plugin_data=self.base)
        self.assertEqual(result['plugin']['installed'], 'DETECTED')
        self.assertEqual(result['skills']['enabled_count'], 14)
        self.assertEqual(result['hook_trust'], 'UNTRUSTED')
        self.assertEqual(result['context_emitted'], 'OBSERVED_HISTORY')
        self.assertEqual(result['method_application'], 'NOT_OBSERVED')
        self.assertFalse(result['native_ready'])
        with patch('cdf_runtime.hooks.app_server', lambda *a, **k: self.server(trusted=True)):
            result = runtime_status('fake', cwd=self.base)
        self.assertEqual(result['state'], 'READY_NOT_EXECUTION_PROOF')
        self.assertEqual(result['observed'], 'NOT_OBSERVED')
        with patch('cdf_runtime.hooks.app_server', lambda *a, **k: self.server(trusted=True, duplicate=True)):
            result = runtime_status('fake', cwd=self.base)
        self.assertFalse(result['native_ready'])
        with patch('cdf_runtime.hooks.app_server', lambda *a, **k: self.server(trusted=True, unexpected=True)):
            result = runtime_status('fake', cwd=self.base)
        self.assertFalse(result['native_ready'])

    def test_unavailable_runtime_and_unsafe_history_do_not_claim_activation(self):
        (self.base / 'events.jsonl').write_text('invalid')
        with patch('cdf_runtime.hooks.app_server', side_effect=ValueError):
            result = runtime_status('fake', cwd=self.base, plugin_data=self.base)
        self.assertEqual(result['plugin']['installed'], 'UNKNOWN')
        self.assertEqual(result['hook_trust'], 'UNKNOWN')
        self.assertEqual(result['context_emitted'], 'NOT_OBSERVED')
        self.assertEqual(result['state'], 'DEGRADED')

    def test_single_identity_and_known_client_compatibility(self):
        for index, profile in enumerate(('standard', 'portable', 'desktop-controlled')):
            output = self.base / str(index)
            build_plugin(output, profile=profile)
            root = json.loads((output / 'plugin.json').read_text())
            fallback = json.loads((output / '.codex-plugin/plugin.json').read_text())
            self.assertEqual(root['name'], fallback['name'])
            self.assertEqual(root['name'], 'code-delivery-framework')
            self.assertEqual(root['extensions']['com.openai']['hooks'], fallback['hooks'])
            hooks = json.loads((output / 'hooks/hooks.json').read_text())['hooks']
            self.assertEqual(set(hooks), set(CONTEXTS))
            self.assertTrue(all(len(groups) == 1 and len(groups[0]['hooks']) == 1 for groups in hooks.values()))
        with patch('scripts.package_cdf_plugin.client_version', return_value='codex-cli 0.169.0-alpha.11.1'):
            output = self.base / 'compatibility'; build_plugin(output, codex='fake')
        self.assertFalse((output / 'plugin.json').exists())
        self.assertTrue((output / '.codex-plugin/plugin.json').is_file())


if __name__ == '__main__':
    unittest.main()
