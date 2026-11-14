"""Native profile ownership/recovery contracts; fake catalogs are not model runs."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cdf_installer import core
from cdf_installer.agents import perform_profile, RECEIPT
from cdf_runtime.policy import native_profile_plan
from cdf_registry import PROFILE_AGENTS

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / 'policies/native-agents.example.toml'


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class NativeProfiles(unittest.TestCase):
    def setUp(self):
        self.tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.target = Path(self.tmp).resolve()
        self.enterContext(patch.object(Path, 'home', return_value=self.target / 'home'))
        self.enterContext(patch.dict('os.environ', {'CODEX_HOME': str(self.target / 'home/.codex')}))
        self.draft = native_profile_plan(POLICY)
        pairs = [(r['model_requested'], r['effort_requested']) for r in self.draft['roles'].values()]
        self.ready = native_profile_plan(POLICY, capabilities={'pairs': pairs, 'agents_enabled': True})

    def test_draft_is_read_only_and_catalog_is_not_runtime_confirmation(self):
        before = snapshot(self.target)
        result = perform_profile(self.target, 'project', self.draft)
        self.assertEqual(snapshot(self.target), before)
        self.assertFalse(result['proposal']['native_config_applied'])
        self.assertEqual(result['proposal']['runtime_routing'], 'NOT_OBSERVED')
        self.assertEqual({r['state'] for r in self.ready['roles'].values()}, {'AVAILABLE_ADVERTISED'})
        self.assertTrue(all(r['model_observed'] is None for r in self.ready['roles'].values()))
        with self.assertRaises(core.CDFError):
            perform_profile(self.target, 'project', self.draft, dry=False)
        self.assertEqual(snapshot(self.target), before)

    def test_apply_idempotency_update_and_rollback_preserve_user_files(self):
        (self.target / 'AGENTS.md').write_bytes(b'User policy\r\n')
        (self.target / 'notes').write_bytes(b'User data')
        result = perform_profile(self.target, 'project', self.ready, dry=False)
        self.assertEqual(result['state'], 'configured')
        self.assertEqual(result['runtime_routing'], 'NOT_OBSERVED')
        self.assertFalse((self.target / core.MANIFEST).exists())
        before = snapshot(self.target)
        perform_profile(self.target, 'project', self.ready, dry=False)
        self.assertEqual(snapshot(self.target), before)
        pairs = [('gpt-6-luna', 'high'), ('gpt-6.1-sol', 'high')]
        quality = native_profile_plan(POLICY, profile='quality', capabilities={'pairs': pairs, 'agents_enabled': True})
        perform_profile(self.target, 'project', quality, dry=False)
        perform_profile(self.target, 'project', rollback=True, dry=True)
        self.assertTrue((self.target / RECEIPT).is_file())
        perform_profile(self.target, 'project', rollback=True, dry=False)
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(), b'User policy\r\n')
        self.assertEqual((self.target / 'notes').read_bytes(), b'User data')
        self.assertFalse(list((self.target / '.codex/agents').glob('*.toml')))
        self.assertFalse((self.target / '.codex/config.toml').exists())

    def test_foreign_and_modified_roles_block_without_overwrite(self):
        agent = self.target / '.codex/agents/cdf_explorer.toml'
        agent.parent.mkdir(parents=True)
        agent.write_bytes(b'User agent')
        before = snapshot(self.target)
        with self.assertRaises(core.CDFError): perform_profile(self.target, 'project', self.ready, dry=False)
        self.assertEqual(snapshot(self.target), before)
        agent.unlink()
        perform_profile(self.target, 'project', self.ready, dry=False)
        agent.write_bytes(b'User edited generated agent')
        before = snapshot(self.target)
        for rollback in (False, True):
            with self.assertRaises(core.CDFError):
                perform_profile(self.target, 'project', self.ready, rollback=rollback, dry=False)
            self.assertEqual(snapshot(self.target), before)

    def test_preexisting_identical_role_is_not_adopted(self):
        agent = self.target / '.codex/agents/cdf_explorer.toml'
        agent.parent.mkdir(parents=True)
        original = self.ready['roles']['cdf_explorer']['content'].encode()
        agent.write_bytes(original)
        perform_profile(self.target, 'project', self.ready, dry=False)
        self.assertNotIn('cdf_explorer', json.loads((self.target / RECEIPT).read_text())['owned'])
        perform_profile(self.target, 'project', rollback=True, dry=False)
        self.assertEqual(agent.read_bytes(), original)

    def test_missing_capability_and_disabled_agents_fail_before_mutation(self):
        for capabilities in ({'pairs': [], 'agents_enabled': True},
                             {'pairs': [(r['model_requested'], r['effort_requested']) for r in self.ready['roles'].values()], 'agents_enabled': False}):
            unavailable = native_profile_plan(POLICY, capabilities=capabilities)
            self.assertTrue(all(r['state'] == 'UNAVAILABLE' for r in unavailable['roles'].values()))
            before = snapshot(self.target)
            with self.assertRaises(core.CDFError): perform_profile(self.target, 'project', unavailable, dry=False)
            self.assertEqual(snapshot(self.target), before)

    def test_interruption_uses_existing_recover_without_claiming_whole_bundle(self):
        class Crash(BaseException): pass
        apply = core.apply_file
        count = 0
        def interrupt(root, path, data, permissions):
            nonlocal count
            apply(root, path, data, permissions)
            count += 1
            if count == 2: raise Crash()
        with patch.object(core, 'apply_file', side_effect=interrupt), self.assertRaises(Crash):
            perform_profile(self.target, 'project', self.ready, dry=False)
        self.assertTrue((self.target / core.TX).exists())
        self.assertEqual(core.perform(self.target, 'project', 'recover')['state'], 'recovered')
        self.assertFalse((self.target / RECEIPT).exists())
        self.assertFalse(list((self.target / '.codex/agents').glob('*.toml')))
        perform_profile(self.target, 'project', self.ready, dry=False)
        self.assertTrue((self.target / RECEIPT).is_file())

    def test_legacy_manifest_and_symlink_paths_are_not_repurposed(self):
        directory = self.target / '.codex/cdf'
        directory.mkdir(parents=True)
        (self.target / core.MANIFEST).write_text('{}')
        with self.assertRaises(core.CDFError): perform_profile(self.target, 'project', self.ready, dry=False)
        (self.target / core.MANIFEST).unlink()
        (self.target / '.codex/agents').symlink_to(self.target / 'elsewhere')
        with self.assertRaises(core.CDFError): perform_profile(self.target, 'project', self.ready, dry=False)

    def test_concurrent_edit_between_ownership_check_and_op_is_not_adopted(self):
        from cdf_installer import agents
        perform_profile(self.target, 'project', self.ready, dry=False)
        path = self.target / '.codex/agents/cdf_reviewer.toml'
        original = path.read_bytes()
        quality = native_profile_plan(POLICY, profile='quality', capabilities={
            'pairs': [('gpt-6-luna', 'high'), ('gpt-6.1-sol', 'high')], 'agents_enabled': True})
        real_op = agents._op
        for rollback in (False, True):
            with self.subTest(rollback=rollback):
                path.write_bytes(original)
                count = 0
                def race(root, relative, *args, **kwargs):
                    nonlocal count
                    if relative == '.codex/agents/cdf_reviewer.toml':
                        count += 1
                        if count == 2:
                            path.write_bytes(b'Concurrent user edit')
                    return real_op(root, relative, *args, **kwargs)
                with patch.object(agents, '_op', side_effect=race), self.assertRaises(core.CDFError) as error:
                    perform_profile(self.target, 'project', quality, rollback=rollback, dry=False)
                self.assertEqual(error.exception.code, 'CONCURRENT_MUTATION')
                self.assertEqual(path.read_bytes(), b'Concurrent user edit')

    def test_cli_unavailable_check_is_nonzero_and_never_applies_fallback(self):
        import io
        from contextlib import redirect_stdout
        from scripts.cdf import main
        output = io.StringIO()
        with patch('cdf_runtime.codex.model_capabilities', return_value={
                'source': 'synthetic_test_catalog', 'pairs': [], 'agents_enabled': True}), redirect_stdout(output):
            code = main(['profile', '--check', '--target', str(self.target), '--policy', str(POLICY),
                         '--codex', '/synthetic/codex', '--json'])
        self.assertEqual(code, 4)
        result = json.loads(output.getvalue())
        self.assertEqual(result['state'], 'unavailable')
        self.assertEqual(result['runtime_routing'], 'NOT_OBSERVED')
        self.assertTrue(all(role['model_observed'] is None for role in result['proposal']['roles'].values()))
        self.assertEqual(snapshot(self.target), {})

    def test_cli_local_collision_is_checked_before_native_query(self):
        import io
        from contextlib import redirect_stdout
        from scripts.cdf import main
        agent = self.target / '.codex/agents/cdf_explorer.toml'
        agent.parent.mkdir(parents=True)
        agent.write_text('User-owned agent')
        before = snapshot(self.target)
        with patch('cdf_runtime.codex.model_capabilities') as query, redirect_stdout(io.StringIO()):
            code = main(['profile', '--apply', '--target', str(self.target), '--policy', str(POLICY), '--json'])
        self.assertNotEqual(code, 0)
        query.assert_not_called()
        self.assertEqual(snapshot(self.target), before)

    def test_cli_global_setup_preserves_config_and_uses_selected_home(self):
        import io
        from contextlib import redirect_stdout
        from scripts.cdf import main
        home = self.target / 'selected-home'
        (home / '.codex').mkdir(parents=True)
        config = home / '.codex/config.toml'
        original = b'# User-owned settings\n[agents]\nenabled = true\n'
        config.write_bytes(original)
        capabilities = {'pairs': [(r['model_requested'], r['effort_requested']) for r in self.ready['roles'].values()], 'agents_enabled': True}
        with patch('cdf_runtime.codex.model_capabilities', return_value=capabilities) as query, redirect_stdout(io.StringIO()):
            code = main(['profile', '--apply', '--scope', 'global', '--target', str(home), '--home', str(home),
                         '--policy', str(POLICY), '--codex', '/synthetic/codex', '--json'])
        self.assertEqual(code, 0)
        self.assertEqual(query.call_args.kwargs['env']['HOME'], str(home))
        self.assertEqual(query.call_args.kwargs['env']['CODEX_HOME'], str(home / '.codex'))
        self.assertEqual(config.read_bytes(), original)
        with redirect_stdout(io.StringIO()):
            code = main(['profile', '--rollback', '--scope', 'global', '--target', str(home), '--home', str(home)])
        self.assertEqual(code, 0)
        self.assertEqual(config.read_bytes(), original)
        self.assertFalse(list((home / '.codex/agents').glob('*.toml')))
