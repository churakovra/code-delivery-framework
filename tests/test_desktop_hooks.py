"""Local privacy/lifecycle checks; not native hook execution evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import contextmanager

from hooks.observe import observe, LIMIT
from cdf_runtime.hooks import runtime_status
from scripts.package_cdf_plugin import build_plugin


class DesktopHooks(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.payload = {'hook_event_name': 'SubagentStart', 'session_id': 'parent-1',
                        'agent_id': 'child-1', 'agent_type': 'cdf_explorer', 'model': 'test-model',
                        'tool_input': {'command': 'SECRET'}, 'transcript_path': '/SECRET',
                        'last_assistant_message': 'SECRET', 'reasoning_effort': 'high'}

    def test_allowlist_and_no_inferred_effort(self):
        row = observe(self.payload, self.base)
        raw = (self.base / 'events.jsonl').read_text()
        self.assertNotIn('SECRET', raw)
        self.assertIsNone(row['effort_observed'])
        self.assertEqual(row['model_observed'], 'test-model')
        self.assertEqual((self.base / 'events.jsonl').stat().st_mode & 0o777, 0o600)

    def test_symlink_fifo_full_logs_are_preserved(self):
        protected = self.base / 'protected'; protected.write_text('keep')
        log = self.base / 'events.jsonl'; log.symlink_to(protected)
        with self.assertRaises(OSError): observe(self.payload, self.base)
        self.assertEqual(protected.read_text(), 'keep')
        log.unlink()
        import os
        os.mkfifo(log)
        with self.assertRaises(OSError): observe(self.payload, self.base)
        log.unlink(); log.write_bytes(b'x' * LIMIT)
        with self.assertRaises(ValueError): observe(self.payload, self.base)
        self.assertEqual(log.stat().st_size, LIMIT)

    def test_missing_or_malformed_input_does_not_create_log(self):
        for payload in ({}, [], dict(self.payload, session_id='secret with spaces')):
            with self.assertRaises(ValueError): observe(payload, self.base)
        self.assertFalse((self.base / 'events.jsonl').exists())

    def test_discovery_is_not_execution_and_history_is_not_current_readiness(self):
        trusted = False
        @contextmanager
        def server(*a, **kw):
            yield lambda *args: {'data': [{'hooks': [
                {'pluginId': 'code-delivery-framework-desktop@local', 'eventName': event,
                 'enabled': True, 'trustStatus': 'trusted' if trusted else 'untrusted', 'source': 'plugin'}
                for event in ('sessionStart', 'subagentStart', 'subagentStop')],
                'warnings': [], 'errors': []}]}, {'userAgent': 'fake'}
        observe(self.payload, self.base)
        with patch('cdf_runtime.hooks.app_server', server):
            report = runtime_status('fake', cwd=self.base, plugin_data=self.base, session_id='parent-1')
        self.assertEqual(report['state'], 'DEGRADED')
        self.assertEqual(report['discovered'], 'DETECTED')
        self.assertEqual(report['observed'], 'OBSERVED_HISTORY')
        self.assertEqual(report['enforcement'], 'NOT_PROVIDED')
        self.assertNotIn('SECRET', json.dumps(report))
        (self.base / 'events.jsonl').write_text('malformed')
        trusted = True
        with patch('cdf_runtime.hooks.app_server', server):
            broken = runtime_status('fake', cwd=self.base, plugin_data=self.base)
        self.assertTrue(broken['native_ready'])
        self.assertEqual(broken['state'], 'DEGRADED')
        with patch('cdf_runtime.hooks.app_server', side_effect=ValueError):
            report = runtime_status('fake', cwd=self.base, plugin_data=self.base)
        self.assertEqual(report['state'], 'DEGRADED')
        self.assertEqual(report['observed'], 'NOT_OBSERVED')

    def test_valid_full_history_is_preserved_but_observer_is_degraded(self):
        @contextmanager
        def server(*a, **kw):
            yield lambda *args: {'data': [{'hooks': [
                {'pluginId': 'code-delivery-framework-desktop@local', 'eventName': event,
                 'enabled': True, 'trustStatus': 'trusted', 'source': 'plugin'}
                for event in ('sessionStart', 'subagentStart', 'subagentStop')],
                'warnings': [], 'errors': []}]}, {}
        line = json.dumps({'schema': 1, 'source': 'observed_hook',
                           'event': 'SessionStart', 'session_id': 'parent-1'}).encode()
        samples = (line + b' ' * (LIMIT - len(line) - 1) + b'\n',
                   (line + b'\n') * (LIMIT // (len(line) + 1) + 1))
        for raw in samples:
            with self.subTest(size=len(raw)):
                (self.base / 'events.jsonl').write_bytes(raw)
                with self.assertRaises(ValueError): observe(self.payload, self.base)
                with patch('cdf_runtime.hooks.app_server', server):
                    report = runtime_status('fake', cwd=self.base, plugin_data=self.base)
                self.assertTrue(report['native_ready'])
                self.assertEqual(report['state'], 'DEGRADED')
                self.assertEqual(report['observed'], 'OBSERVED_HISTORY')
                self.assertGreater(report['recorded_events']['SessionStart'], 0)
                self.assertEqual((self.base / 'events.jsonl').read_bytes(), raw)

    def test_history_path_is_not_configuration_evidence(self):
        @contextmanager
        def server(*a, **kw):
            yield lambda *args: {'data': []}, {}
        with patch('cdf_runtime.hooks.app_server', server):
            report = runtime_status('fake', cwd=self.base, plugin_data=self.base / 'absent')
        self.assertEqual(report['configured'], 'NOT_OBSERVED')
        self.assertEqual(report['discovered'], 'NOT_OBSERVED')
        self.assertEqual(report['state'], 'DEGRADED')

    def test_desktop_is_separate_opt_in_portable_stays_hook_free(self):
        portable = self.base / 'portable'; desktop = self.base / 'desktop'
        build_plugin(portable)
        build_plugin(desktop, profile='desktop-controlled')
        self.assertFalse((portable / 'hooks').exists())
        self.assertNotIn('hooks', json.loads((portable / 'plugin.json').read_text())['extensions']['com.openai'])
        self.assertFalse((desktop / 'plugin.json').exists())
        manifest = json.loads((desktop / '.codex-plugin/plugin.json').read_text())
        self.assertEqual(manifest['name'], 'code-delivery-framework-desktop')
        self.assertEqual(manifest['hooks'], './hooks/hooks.json')
        self.assertEqual({p.relative_to(portable / 'skills') for p in (portable / 'skills').rglob('SKILL.md')},
                         {p.relative_to(desktop / 'skills') for p in (desktop / 'skills').rglob('SKILL.md')})

    def test_session_context_is_compact_detected_metadata_not_runtime_routing(self):
        from hooks.observe import session_context
        root = self.base / 'plugin'; (root / '.codex-plugin').mkdir(parents=True)
        (root / '.codex-plugin/plugin.json').write_text('{"version":"2.0.0-rc1"}')
        project = self.base / 'project'
        (project / '.codex/cdf/backups').mkdir(parents=True)
        (project / '.codex/cdf/backups/native-agents.json').write_text(
            '{"schema":1,"profile":"balanced","other":"SECRET"}')
        with patch('hooks.observe.__file__', str(root / 'hooks/observe.py')):
            context = session_context({'cwd': str(project), 'transcript_path': '/SECRET'})
        self.assertEqual(context['bundle_version_detected'], '2.0.0-rc1')
        self.assertEqual(context['profile_configured'], 'balanced')
        self.assertEqual(context['role_files'], 'incomplete')
        self.assertEqual(context['routing'], 'NOT_OBSERVED')
        self.assertEqual(context['agent_availability'], 'NOT_CHECKED')
        self.assertNotIn('SECRET', json.dumps(context))
        self.assertLess(len(json.dumps(context)), 512)

    def test_session_start_wire_output_is_bounded_and_other_events_stay_empty(self):
        import os
        import subprocess
        import sys
        script = Path(__file__).resolve().parents[1] / 'hooks/observe.py'
        env = dict(os.environ, PLUGIN_DATA=str(self.base))
        payload = dict(self.payload, hook_event_name='SessionStart', cwd=str(self.base))
        result = subprocess.run([sys.executable, str(script)], input=json.dumps(payload),
                                text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)['hookSpecificOutput']
        self.assertEqual(output['hookEventName'], 'SessionStart')
        self.assertIn('not verified', output['additionalContext'])
        self.assertLess(len(result.stdout.encode()), 1024)
        self.assertNotIn('SECRET', result.stdout)
        result = subprocess.run([sys.executable, str(script)], input=json.dumps(self.payload),
                                text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(json.loads(result.stdout), {})
