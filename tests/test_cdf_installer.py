"""Behavioral checks for offline CDF 2 lifecycle in disposable targets."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cdf_installer import core

ROOT = Path(__file__).resolve().parents[1]


def fake_bundle(root):
    for name in core.CORE + sum(core.EXTRAS.values(), ()):
        path = root / 'skills' / name
        path.mkdir(parents=True)
        (path / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Test skill.\n---\nContent.\n')
    templates = root / 'templates'
    templates.mkdir()
    (templates / 'AGENTS.cdf-block.md').write_bytes(core.START + b'\nmanaged instructions\n' + core.END + b'\n')
    for name in ('cdf_reviewer', 'cdf_diagnostician'):
        (templates / f'{name}.toml').write_text(f'name = "{name}"\ndescription = "Role"\ndeveloper_instructions = "Check changes"\n')
    (root / 'subskills.catalog.json').write_text(json.dumps({'candidates': {'codebase-memory-mcp': {'source_url': 'https://example.com', 'revision': 'a'*40, 'license_note': 'MIT'}}}))
    (root / 'pyproject.toml').write_text('[project]\nversion = "2.0.0.dev0"\n')


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.target = self.base / 'project'
        self.target.mkdir()
        self.src = self.base / 'bundle'
        self.src.mkdir()
        self.fake_home = self.base / 'user-home'
        self.fake_home.mkdir()
        home_patch = patch.object(core.Path, 'home', return_value=self.fake_home)
        home_patch.start()
        self.addCleanup(home_patch.stop)
        isolated_codex = self.base / 'isolated-codex-home'
        codex_patch = patch.dict(os.environ, {'CODEX_HOME': str(isolated_codex)})
        codex_patch.start()
        self.addCleanup(codex_patch.stop)
        fake_bundle(self.src)

    def action(self, name, **kw):
        return core.perform(self.target, 'project', name, src=self.src, **kw)

    def test_dry_run_and_round_trip_preserve_unterminated_agents(self):
        agents = self.target / 'AGENTS.md'
        agents.write_bytes(b'Existing user text')
        before = {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        plan = self.action('install', dry=True)
        self.assertEqual(plan['state'], 'ready')
        self.assertEqual(before, {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob('*') if p.is_file()})
        self.assertEqual(self.action('install')['state'], 'installed')
        self.assertEqual(len(list((self.target / '.agents/skills').glob('*/SKILL.md'))), 12)
        self.assertEqual(core.status(self.target, 'project')['files'], 'clean')
        self.assertEqual(core.status(self.target, 'project')['skills_discovery'], 'unverified')
        self.assertEqual(self.action('uninstall')['state'], 'absent')
        self.assertEqual(agents.read_bytes(), b'Existing user text')

    def test_created_agents_removed_but_existing_empty_file_preserved(self):
        self.action('install')
        self.action('uninstall')
        self.assertFalse((self.target / 'AGENTS.md').exists())
        (self.target / 'AGENTS.md').touch()
        self.action('install')
        self.action('uninstall')
        self.assertTrue((self.target / 'AGENTS.md').exists())

    def test_installed_manifest_must_include_core_skills_agents_block_and_extras(self):
        self.action('install')
        manifest = self.target / core.MANIFEST
        original = json.loads(manifest.read_text())
        broken_variants = []
        empty = dict(original, owned_files={}, managed_blocks={}, preserved_preimages={})
        broken_variants.append(empty)
        missing_core = json.loads(json.dumps(original))
        del missing_core['owned_files']['.agents/skills/cdf-backend/SKILL.md']
        broken_variants.append(missing_core)
        missing_agent = json.loads(json.dumps(original))
        del missing_agent['owned_files']['.codex/agents/cdf_reviewer.toml']
        broken_variants.append(missing_agent)
        missing_extra = json.loads(json.dumps(original))
        missing_extra['selected_extras'] = ['learning']
        broken_variants.append(missing_extra)
        for broken in broken_variants:
            with self.subTest(variant=broken):
                manifest.write_text(json.dumps(broken))
                with self.assertRaises(core.CDFError) as caught:
                    core.status(self.target, 'project')
                self.assertEqual(caught.exception.code, 'MANIFEST_UNSUPPORTED')

    def test_global_codex_home_and_ancestor_skills_collisions_are_reported(self):
        for location in ('home', 'codex_home', 'ancestor'):
            with self.subTest(location=location), tempfile.TemporaryDirectory(dir=self.base) as d:
                selected_project = Path(d).resolve() / 'parent' / 'project'
                selected_project.mkdir(parents=True)
                codex_home = Path(d).resolve() / 'codex-home'
                fake_home = Path(d).resolve() / 'home'
                roots = {'home': fake_home / '.agents/skills',
                         'codex_home': codex_home / 'skills',
                         'ancestor': selected_project.parent / '.agents/skills'}
                duplicate = roots[location] / 'elsewhere' / 'SKILL.md'
                duplicate.parent.mkdir(parents=True)
                duplicate.write_text('---\nname: cdf-backend\ndescription: existing\n---\n')
                with patch.object(core.Path, 'home', return_value=fake_home), \
                     patch.dict(os.environ, {'CODEX_HOME': str(codex_home)}):
                    with self.assertRaises(core.CDFError) as caught:
                        core.perform(selected_project, 'project', 'install', dry=True, src=self.src)
                self.assertEqual(caught.exception.code, 'PATH_COLLISION')
                self.assertEqual(caught.exception.paths, [str(duplicate)])
                self.assertEqual(duplicate.read_text(), '---\nname: cdf-backend\ndescription: existing\n---\n')
                self.assertEqual(list(selected_project.iterdir()), [])

    def test_global_upgrade_does_not_conflict_with_its_owned_skills(self):
        core.perform(self.target, 'global', 'install', src=self.src)
        self.assertEqual(core.perform(self.target, 'global', 'upgrade', src=self.src)['state'], 'installed')

    def test_downgrade_from_newer_or_final_version_is_refused_without_writes(self):
        self.action('install')
        manifest = self.target / core.MANIFEST
        for installed_version in ('2.9.0', '2.0.0'):
            with self.subTest(installed_version=installed_version):
                value = json.loads(manifest.read_text())
                value['framework_version'] = installed_version
                manifest.write_text(json.dumps(value))
                before = {p.relative_to(self.target).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o7777)
                          for p in self.target.rglob('*') if p.is_file()}
                with self.assertRaises(core.CDFError) as caught:
                    self.action('upgrade')
                self.assertEqual(caught.exception.code, 'MANIFEST_UNSUPPORTED')
                self.assertEqual(before, {p.relative_to(self.target).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o7777)
                                          for p in self.target.rglob('*') if p.is_file()})
                self.assertFalse((self.target / core.LOCK).exists())
                self.assertFalse((self.target / core.TX).exists())

    def test_forward_development_version_upgrade_is_allowed(self):
        self.action('install')
        (self.src / 'pyproject.toml').write_text('[project]\nversion = "2.0.0.dev1"\n')
        self.assertEqual(self.action('upgrade')['state'], 'installed')
        self.assertEqual(core.manifest_read(self.target, 'project')['framework_version'], '2.0.0.dev1')
        (self.src / 'pyproject.toml').write_text('[project]\nversion = "2.0.0"\n')
        self.assertEqual(self.action('upgrade')['state'], 'installed')
        self.assertEqual(core.manifest_read(self.target, 'project')['framework_version'], '2.0.0')

    def test_upgrade_extras_preserves_and_removes_owned_skills(self):
        self.action('install', enable=['learning'])
        self.action('upgrade', enable=['operator'])
        self.assertEqual(len(list((self.target / '.agents/skills').glob('*/SKILL.md'))), 15)
        self.action('upgrade', disable=['learning'])
        self.assertEqual(len(list((self.target / '.agents/skills').glob('*/SKILL.md'))), 13)
        self.assertFalse((self.target / '.agents/skills/cdf-explain/SKILL.md').exists())
        self.assertEqual(core.manifest_read(self.target, 'project')['selected_extras'], ['operator'])

    def test_upgrade_refuses_modified_owned_file_uninstall_preserves_it(self):
        self.action('install')
        path = self.target / '.agents/skills/cdf-backend/SKILL.md'
        original = path.read_bytes()
        path.write_bytes(b'user edits')
        with self.assertRaises(core.CDFError) as caught:
            self.action('upgrade')
        self.assertEqual(caught.exception.code, 'MANAGED_FILE_MODIFIED')
        result = self.action('uninstall')
        self.assertEqual(result['state'], 'partial')
        self.assertEqual(path.read_bytes(), b'user edits')
        self.assertIn(str(path.relative_to(self.target)), result['preserved'])
        path.write_bytes(original)
        self.assertEqual(self.action('uninstall')['state'], 'absent')

    def test_agents_outside_block_edits_preserved(self):
        agents = self.target / 'AGENTS.md'
        agents.write_bytes(b'old\r\n')
        self.action('install')
        agents.write_bytes(b'new prefix\r\n' + agents.read_bytes() + b'new suffix\r\n')
        self.action('uninstall')
        self.assertEqual(agents.read_bytes(), b'new prefix\r\nold\r\nnew suffix\r\n')

    def test_modified_agents_block_is_preserved_and_uninstall_resumable(self):
        self.action('install')
        agents = self.target / 'AGENTS.md'
        original = agents.read_bytes()
        agents.write_bytes(original.replace(b'managed instructions', b'user modified'))
        result = self.action('uninstall')
        self.assertEqual(result['state'], 'partial')
        self.assertIn('AGENTS.md', result['preserved'])
        agents.write_bytes(original)
        self.assertEqual(self.action('uninstall')['state'], 'absent')

    def test_name_collision_and_legacy_block_prevent_any_payload_write(self):
        skill = self.target / '.agents/skills/other/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('---\nname: cdf-backend\ndescription: mine\n---\n')
        with self.assertRaises(core.CDFError) as caught: self.action('install')
        self.assertEqual(caught.exception.code, 'PATH_COLLISION')
        self.assertFalse((self.target / core.MANIFEST).exists())
        skill.unlink()
        (self.target / 'AGENTS.md').write_bytes(b'<!-- codex-delivery-framework:start -->\nold\n')
        with self.assertRaises(core.CDFError) as caught: self.action('install')
        self.assertEqual(caught.exception.code, 'LEGACY_MIGRATION_REQUIRED')

    def test_symlink_traversal_and_tampered_manifest_refused(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (self.target / '.agents').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(core.CDFError): self.action('install')
        self.assertEqual(list(outside.iterdir()), [])
        (self.target / '.agents').unlink()
        self.action('install')
        manifest = self.target / core.MANIFEST
        value = json.loads(manifest.read_text())
        value['owned_files']['../outside/important'] = {'sha256': 'a'*64, 'mode': 420}
        manifest.write_text(json.dumps(value))
        with self.assertRaises(core.CDFError): self.action('uninstall')

    def test_only_installer_created_empty_directories_are_removed(self):
        preexisting = self.target / '.agents/skills'
        preexisting.mkdir(parents=True)
        self.action('install')
        manifest = core.manifest_read(self.target, 'project')
        self.assertNotIn('.agents', manifest['created_directories'])
        self.assertNotIn('.agents/skills', manifest['created_directories'])
        self.assertIn('.agents/skills/cdf-backend', manifest['created_directories'])
        retained = self.target / '.agents/skills/cdf-frontend/user-note.txt'
        retained.write_text('user data')
        self.action('uninstall')
        self.assertTrue(preexisting.is_dir())
        self.assertEqual(retained.read_text(), 'user data')
        self.assertFalse((self.target / '.agents/skills/cdf-backend').exists())
        self.assertFalse((self.target / '.codex').exists())

    def test_recovery_cleans_only_recorded_directories(self):
        real_apply = core.apply_file
        def crash_after_first(*args):
            real_apply(*args)
            raise KeyboardInterrupt('crash during install')
        with patch.object(core, 'apply_file', side_effect=crash_after_first):
            with self.assertRaises(KeyboardInterrupt): self.action('install')
        journal = json.loads((self.target / core.TX / 'journal.json').read_text())
        self.assertIn('.agents/skills/cdf-backend', journal['created_directories'])
        user_file = self.target / '.agents/skills/cdf-frontend/user-note'
        user_file.write_text('preserve')
        self.assertEqual(self.action('recover')['state'], 'recovered')
        self.assertEqual(user_file.read_text(), 'preserve')
        self.assertFalse((self.target / '.agents/skills/cdf-backend').exists())
        self.assertFalse((self.target / '.codex').exists())

    def test_committed_uninstall_cleanup_interruption_is_recoverable(self):
        self.action('install')
        with patch.object(core, 'cleanup_directories', side_effect=KeyboardInterrupt('crash during cleanup')):
            with self.assertRaises(KeyboardInterrupt): self.action('uninstall')
        self.assertEqual(core.status(self.target, 'project')['state'], 'recovery-required')
        self.assertEqual(self.action('recover')['state'], 'recovered')
        self.assertFalse((self.target / '.agents').exists())
        self.assertFalse((self.target / '.codex').exists())

    def test_recovery_after_journal_removal_finishes_directory_cleanup(self):
        self.action('install')
        real_cleanup = core.cleanup_directories
        def crash_after_journal_removal(root, values):
            if values and not (root / core.TX).exists():
                raise KeyboardInterrupt('crash after journal cleanup')
            return real_cleanup(root, values)
        with patch.object(core, 'cleanup_directories', side_effect=crash_after_journal_removal):
            with self.assertRaises(KeyboardInterrupt): self.action('uninstall')
        self.assertFalse((self.target / core.TX).exists())
        self.assertTrue((self.target / core.CLEANUP).is_file())
        self.assertEqual(core.status(self.target, 'project')['state'], 'recovery-required')
        self.assertEqual(self.action('recover')['state'], 'recovered')
        self.assertFalse((self.target / core.CLEANUP).exists())
        self.assertFalse((self.target / '.agents').exists())
        self.assertFalse((self.target / '.codex').exists())

    def test_cleanup_intent_is_recoverable_after_atomic_publish_interruption(self):
        self.action('install')
        real_link = os.link
        def crash_after_link(*args, **kwargs):
            real_link(*args, **kwargs)
            raise KeyboardInterrupt('crash after publishing cleanup intent')
        with patch.object(core.os, 'link', side_effect=crash_after_link):
            with self.assertRaises(KeyboardInterrupt): self.action('uninstall')
        self.assertTrue((self.target / core.TX / 'journal.json').exists())
        self.assertTrue((self.target / core.CLEANUP).exists())
        self.assertEqual(self.action('recover')['state'], 'recovered')
        self.assertFalse((self.target / core.CLEANUP).exists())
        self.assertFalse((self.target / '.codex').exists())

    def test_recovery_after_journal_removal_uses_cleanup_intent(self):
        (self.target / 'AGENTS.md').write_bytes(b'existing')
        self.action('install')
        real_unlink = Path.unlink
        def crash_backup(path, *args, **kwargs):
            if path.parent == self.target / core.TX and path.name.startswith('backup-'):
                raise KeyboardInterrupt('crash after journal removal')
            return real_unlink(path, *args, **kwargs)
        with patch.object(Path, 'unlink', crash_backup):
            with self.assertRaises(KeyboardInterrupt): self.action('uninstall')
        self.assertFalse((self.target / core.TX / 'journal.json').exists())
        self.assertTrue((self.target / core.CLEANUP).exists())
        self.assertEqual(self.action('recover')['state'], 'recovered')
        self.assertEqual((self.target / 'AGENTS.md').read_bytes(), b'existing')
        self.assertFalse((self.target / '.codex').exists())

    def test_failure_after_journal_cleanup_stays_recoverable(self):
        self.action('install')
        real_cleanup = core.cleanup_directories
        count = 0
        def fail_after_lock(root, values):
            nonlocal count
            count += 1
            if count == 3: raise OSError('injected final cleanup failure')
            return real_cleanup(root, values)
        with patch.object(core, 'cleanup_directories', side_effect=fail_after_lock):
            with self.assertRaises(OSError): self.action('uninstall')
        self.assertFalse((self.target / core.TX).exists())
        self.assertTrue((self.target / core.CLEANUP).is_file())
        self.assertEqual(core.status(self.target, 'project')['state'], 'recovery-required')
        self.assertEqual(self.action('recover')['state'], 'recovered')
        self.assertFalse((self.target / core.CLEANUP).exists())

    def test_unowned_cleanup_marker_is_preserved(self):
        marker = self.target / core.CLEANUP
        marker.write_text('user-owned')
        with self.assertRaises(core.CDFError): self.action('install')
        self.assertEqual(marker.read_text(), 'user-owned')
        self.assertEqual(core.status(self.target, 'project')['state'], 'recovery-required')
        with self.assertRaises(core.CDFError): self.action('recover')
        self.assertEqual(marker.read_text(), 'user-owned')

    def test_cleanup_failure_never_reports_absent_and_remains_recoverable(self):
        self.action('install')
        with patch.object(core, 'cleanup_directories', side_effect=OSError('injected cleanup failure')):
            with self.assertRaises(OSError): self.action('uninstall')
        self.assertEqual(core.status(self.target, 'project')['state'], 'recovery-required')
        self.assertEqual(self.action('recover')['state'], 'recovered')

    def test_legacy_external_mcp_metadata_is_reported_without_opening_binary(self):
        external = self.base / 'outside-binary'
        external.write_bytes(b'sensitive external binary')
        reused = self.target / '.agents/skills/reused/SKILL.md'
        reused.parent.mkdir(parents=True)
        reused.write_bytes(b'user-owned reused skill')
        mpath = self.target / '.codex/delivery-framework/manifest.json'
        mpath.parent.mkdir(parents=True)
        mpath.write_text(json.dumps({'framework_version': '0.6.0', 'state': 'installed', 'files': {},
            'reused': {str(reused.relative_to(self.target)): core.digest(reused.read_bytes())},
            'external_mcp': {'path': str(external), 'sha256': 'b' * 64,
                             'config': {'command': str(external), 'args': []}}}))
        real_read = Path.read_bytes
        def forbid_external(path):
            if path == external: raise AssertionError('external binary must not be read')
            return real_read(path)
        with patch.object(Path, 'read_bytes', forbid_external):
            report = core.legacy_report(self.target, 'project')
        info = report['legacy_manifest']
        self.assertEqual(info['external_mcp']['ownership'], 'external-unowned')
        self.assertEqual(info['external_mcp']['verification'], 'not-checked')
        self.assertEqual(info['reused'][str(reused.relative_to(self.target))], 'clean')
        malformed = json.loads(mpath.read_text())
        malformed['external_mcp']['path'] = '../escape'
        mpath.write_text(json.dumps(malformed))
        self.assertEqual(core.legacy_report(self.target, 'project')['legacy_manifest']['external_mcp']['state'], 'invalid')

    def test_case_collision_fails_preflight(self):
        (self.target / '.Agents').mkdir()
        with self.assertRaises(core.CDFError) as caught: self.action('install', dry=True)
        self.assertEqual(caught.exception.code, 'PATH_COLLISION')

    def test_crash_after_each_early_replacement_recovers_original(self):
        for fail_at in (0, 1, 5, 14):
            with self.subTest(fail_at=fail_at), tempfile.TemporaryDirectory(dir=self.base) as d:
                root = Path(d).resolve()
                agents = root / 'AGENTS.md'
                agents.write_bytes(b'before')
                real = core.apply_file
                calls = 0
                def crash(*args):
                    nonlocal calls
                    if calls == fail_at: raise KeyboardInterrupt('simulated kill')
                    calls += 1
                    return real(*args)
                with patch.object(core, 'apply_file', side_effect=crash):
                    with self.assertRaises(KeyboardInterrupt): core.perform(root, 'project', 'install', src=self.src)
                self.assertEqual(core.status(root, 'project')['state'], 'recovery-required')
                self.assertEqual(core.perform(root, 'project', 'recover', dry=True)['state'], 'ready')
                self.assertEqual(core.perform(root, 'project', 'recover')['state'], 'recovered')
                self.assertEqual(agents.read_bytes(), b'before')
                self.assertFalse((root / core.MANIFEST).exists())
                self.assertFalse((root / '.agents/skills/cdf-backend/SKILL.md').exists())

    def test_malformed_journal_recovery_preserves_transaction(self):
        agents = self.target / 'AGENTS.md'
        agents.write_bytes(b'user instructions')
        real = core.apply_file
        count = 0
        def crash(*args):
            nonlocal count
            if count == 2: raise KeyboardInterrupt()
            count += 1
            return real(*args)
        with patch.object(core, 'apply_file', side_effect=crash):
            with self.assertRaises(KeyboardInterrupt): self.action('install')
        journal = self.target / core.TX / 'journal.json'
        original_bytes = journal.read_bytes()
        original = json.loads(original_bytes)
        variants = [dict(original, schema=True), dict(original, phase=42),
                    dict(original, paths=[{'relative_path': 9}]),
                    {k: v for k, v in original.items() if k != 'scope'}]
        def snapshot():
            return {p.relative_to(self.target).as_posix():
                    (p.is_dir(), p.stat().st_mode & 0o7777, None if p.is_dir() else p.read_bytes())
                    for p in self.target.rglob('*')}
        for variant in variants:
            with self.subTest(variant=variant):
                journal.write_text(json.dumps(variant))
                before = snapshot()
                for flags in (['--dry-run'], []):
                    result = subprocess.run([sys.executable, str(ROOT / 'scripts/cdf.py'), 'recover',
                                             '--target', str(self.target), '--json', *flags],
                                            text=True, capture_output=True, timeout=30)
                    self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
                    report = json.loads(result.stdout)
                    if flags:
                        self.assertEqual(report['state'], 'conflict')
                        self.assertIn('RECOVERY_REQUIRED', report['warnings'][0])
                    else:
                        self.assertEqual(report['code'], 'RECOVERY_REQUIRED')
                    self.assertEqual(snapshot(), before)
        journal.write_bytes(original_bytes)
        self.assertEqual(self.action('recover')['state'], 'recovered')
        self.assertEqual(agents.read_bytes(), b'user instructions')

    def test_recovery_refuses_concurrent_edit_and_preserves_bytes(self):
        real = core.apply_file
        count = 0
        def crash(*args):
            nonlocal count
            if count == 2: raise KeyboardInterrupt()
            count += 1
            return real(*args)
        with patch.object(core, 'apply_file', side_effect=crash):
            with self.assertRaises(KeyboardInterrupt): self.action('install')
        journal = json.loads((self.target / core.TX / 'journal.json').read_text())
        first = self.target / journal['paths'][0]['relative_path']
        first.write_bytes(b'concurrent user edit')
        self.assertIn(first.relative_to(self.target).as_posix(), core.status(self.target, 'project')['issues'])
        preview = subprocess.run([sys.executable, str(ROOT / 'scripts/cdf.py'), 'recover', '--target', str(self.target), '--dry-run', '--json'], text=True, capture_output=True, timeout=30)
        self.assertEqual(preview.returncode, 3, preview.stdout + preview.stderr)
        self.assertIn(first.relative_to(self.target).as_posix(), json.loads(preview.stdout)['conflicts'])
        with self.assertRaises(core.CDFError) as caught: self.action('recover')
        self.assertEqual(caught.exception.code, 'CONCURRENT_MUTATION')
        self.assertEqual(first.read_bytes(), b'concurrent user edit')
        self.assertTrue((self.target / core.TX / 'journal.json').exists())

    def test_committed_journal_cleanup_recovery_keeps_installation(self):
        real_unlink = Path.unlink
        def crash_journal(path, *args, **kwargs):
            if path == self.target / core.TX / 'journal.json':
                raise KeyboardInterrupt('crash after commit')
            return real_unlink(path, *args, **kwargs)
        with patch.object(Path, 'unlink', crash_journal):
            with self.assertRaises(KeyboardInterrupt): self.action('install')
        journal = json.loads((self.target / core.TX / 'journal.json').read_text())
        self.assertEqual(journal['phase'], 'complete')
        # Some backups may have been cleaned up before an interruption.
        backup = next((self.target / core.TX).glob('backup-*'), None)
        if backup is not None: backup.unlink()
        self.assertEqual(self.action('recover')['state'], 'recovered')
        self.assertEqual(core.status(self.target, 'project')['state'], 'installed')
        self.assertTrue((self.target / '.agents/skills/cdf-backend/SKILL.md').exists())

    def test_crash_after_journal_removal_finishes_cleanup_without_rollback(self):
        (self.target / 'AGENTS.md').write_text('user text')
        real_unlink = Path.unlink
        def crash_backup(path, *args, **kwargs):
            if path.parent == self.target / core.TX and path.name.startswith('backup-'):
                raise KeyboardInterrupt('crash during cleanup')
            return real_unlink(path, *args, **kwargs)
        with patch.object(Path, 'unlink', crash_backup):
            with self.assertRaises(KeyboardInterrupt): self.action('install')
        self.assertFalse((self.target / core.TX / 'journal.json').exists())
        self.assertEqual(self.action('recover')['state'], 'recovered')
        self.assertEqual(core.status(self.target, 'project')['state'], 'installed')

    def test_other_native_skill_location_is_collision_checked(self):
        skill = self.target / '.codex/skills/mine/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('---\nname: cdf-backend\ndescription: mine\n---\n')
        with self.assertRaises(core.CDFError) as caught: self.action('install', dry=True)
        self.assertEqual(caught.exception.code, 'PATH_COLLISION')

    def test_bundle_identity_is_digest_and_changes_with_source(self):
        self.action('install')
        first = core.manifest_read(self.target, 'project')['source_revision']
        self.assertRegex(first, r'^sha256:[a-f0-9]{64}$')
        source = self.src / 'skills/cdf-backend/SKILL.md'
        source.write_text(source.read_text() + 'Further content.\n')
        self.action('upgrade')
        self.assertNotEqual(first, core.manifest_read(self.target, 'project')['source_revision'])

    def test_each_replacement_recovers_install_upgrade_and_uninstall(self):
        def files(root):
            return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o7777)
                    for p in root.rglob('*') if p.is_file()}

        for action in ('install', 'upgrade', 'uninstall'):
            with self.subTest(action=action):
                baseline = self.base / ('baseline-' + action)
                baseline.mkdir()
                (baseline / 'AGENTS.md').write_bytes(b'existing instructions')
                (baseline / 'user-data').write_bytes(b'preserve this')
                if action != 'install':
                    core.perform(baseline, 'project', 'install', src=self.src)
                if action == 'upgrade':
                    source = self.src / 'skills/cdf-backend/SKILL.md'
                    source.write_text(source.read_text() + 'New version.\n')
                extras = {'learning'} if action == 'upgrade' else set()
                operations, _, _, _ = core.changes_plan(baseline, 'project', action, extras, self.src)
                # Each case changes the manifest after its file operations.
                replacements = sum(op['operation'] != 'unchanged' for op in operations) + 1
                self.assertGreater(replacements, 1)
                expected = files(baseline)
                for failed_index in range(replacements):
                    with self.subTest(action=action, replacement=failed_index):
                        working = self.base / f'run-{action}-{failed_index}'
                        shutil.copytree(baseline, working)
                        calls = 0
                        real_apply = core.apply_file
                        def crash_after(*args):
                            nonlocal calls
                            real_apply(*args)
                            index = calls
                            calls += 1
                            if index == failed_index:
                                raise KeyboardInterrupt('interrupted after replacement')
                        with patch.object(core, 'apply_file', side_effect=crash_after):
                            with self.assertRaises(KeyboardInterrupt):
                                core.perform(working, 'project', action,
                                             enable=extras, src=self.src)
                        self.assertEqual(core.status(working, 'project')['state'], 'recovery-required')
                        self.assertEqual(core.perform(working, 'project', 'recover')['state'], 'recovered')
                        self.assertEqual(files(working), expected)
                        shutil.rmtree(working)

    def test_subprocess_cannot_install_while_another_process_holds_lock(self):
        with core.Lock(self.target):
            p = subprocess.run([sys.executable, str(ROOT / 'scripts/cdf.py'), 'install',
                                '--target', str(self.target), '--json'],
                               text=True, capture_output=True, timeout=30)
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertEqual(json.loads(p.stdout)['code'], 'CONCURRENT_MUTATION')
            self.assertFalse((self.target / core.MANIFEST).exists())
        self.assertFalse((self.target / core.LOCK).exists())

    def test_journal_directory_entries_are_synced_before_first_payload_write(self):
        synced = []
        real_sync = core.sync_dir
        real_apply = core.apply_file
        first_apply_checked = False
        def record_sync(path):
            synced.append(Path(path))
            return real_sync(path)
        def check_order(*args):
            nonlocal first_apply_checked
            if not first_apply_checked:
                first_apply_checked = True
                self.assertTrue((self.target / core.TX / 'journal.json').is_file())
                self.assertTrue({self.target, self.target / '.codex', self.target / '.codex/cdf',
                                 self.target / core.TX}.issubset(set(synced)))
            return real_apply(*args)
        with patch.object(core, 'sync_dir', side_effect=record_sync), \
             patch.object(core, 'apply_file', side_effect=check_order):
            self.action('install')
        self.assertTrue(first_apply_checked)

    def test_no_network_or_external_process_during_lifecycle(self):
        with patch('socket.socket', side_effect=AssertionError('network')), patch('subprocess.run', side_effect=AssertionError('process')):
            self.action('install')
            self.action('upgrade')
            core.status(self.target, 'project')
            self.action('uninstall')

    def test_global_scope_confines_writes_to_selected_temporary_home(self):
        core.perform(self.target, 'global', 'install', src=self.src)
        self.assertTrue((self.target / '.codex/AGENTS.md').is_file())
        self.assertFalse((self.target / 'AGENTS.md').exists())
        core.perform(self.target, 'global', 'uninstall', src=self.src)
        self.assertFalse((self.target / '.codex/AGENTS.md').exists())

    def test_existing_lock_blocks_concurrent_changes(self):
        lock = self.target / core.LOCK
        lock.mkdir(parents=True)
        with self.assertRaises(core.CDFError) as caught: self.action('install')
        self.assertEqual(caught.exception.code, 'CONCURRENT_MUTATION')
        self.assertFalse((self.target / core.MANIFEST).exists())

    def test_invalid_bundle_dry_run_does_not_write(self):
        (self.src / 'skills/cdf-backend/SKILL.md').write_text('invalid')
        with self.assertRaises(core.CDFError) as caught: self.action('install', dry=True)
        self.assertEqual(caught.exception.code, 'INVALID_BUNDLE')
        self.assertEqual(list(self.target.iterdir()), [])


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp_codex = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_codex.cleanup)
        codex_patch = patch.dict(os.environ, {'CODEX_HOME': str(Path(self.temp_codex.name).resolve())})
        codex_patch.start()
        self.addCleanup(codex_patch.stop)

    def test_invalid_arguments_have_one_json_error(self):
        p = subprocess.run([sys.executable, str(ROOT / 'scripts/cdf.py'), 'install', '--json'], text=True, capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(json.loads(p.stdout)['code'], 'INVALID_REQUEST')
        self.assertEqual(p.stderr, '')

    def test_install_dry_run_conflict_returns_plan_envelope(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d).resolve()
            agent = target / '.codex/agents/cdf_reviewer.toml'
            agent.parent.mkdir(parents=True)
            agent.write_text('user-owned')
            before = agent.read_bytes()
            p = subprocess.run([sys.executable, str(ROOT / 'scripts/cdf.py'), 'install',
                                '--target', str(target), '--dry-run', '--json'],
                               text=True, capture_output=True, timeout=30)
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            result = json.loads(p.stdout)
            self.assertEqual(set(result), {'schema', 'action', 'state', 'scope', 'target',
                                           'planned_actions', 'conflicts', 'warnings'})
            self.assertEqual(result['state'], 'conflict')
            self.assertIn('.codex/agents/cdf_reviewer.toml', result['conflicts'])
            self.assertEqual(agent.read_bytes(), before)
            self.assertFalse((target / core.MANIFEST).exists())

    def test_status_missing_target_is_clean_json_error(self):
        p = subprocess.run([sys.executable, str(ROOT / 'scripts/cdf.py'), 'status', '--target', '/definitely/missing/cdf-target', '--json'], text=True, capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(json.loads(p.stdout)['code'], 'UNSAFE_TARGET')


if __name__ == '__main__': unittest.main()
