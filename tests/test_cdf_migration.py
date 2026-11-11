"""Frozen synthetic 1.1.0 ownership → future inventory, without switching CORE.

M01–M20 are the FINAL pack's migration cases. These tests prove local lifecycle
mechanics, not equivalence to a downloaded release or live skill discovery.
"""
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cdf_installer import core
from cdf_registry import EXTRAS, LEGACY_CORE_11

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/legacy-cdf-11.json'
FIXTURE_SHA256 = '5c7d5489b63d2e0db778a63c7512c6c6871bfe70509f5d42078ce369a292b21b'
FUTURE_CORE = (
    'cdf', 'cdf-backend', 'cdf-code-review', 'cdf-codebase-research',
    'cdf-debugging', 'cdf-documentation', 'cdf-frontend', 'cdf-requirements',
    'cdf-ui-design', 'cdf-verification',
)
RETIRED = ('cdf-implementation', 'cdf-orchestration', 'cdf-planning')


def snapshot(root, timestamps=False):
    """Capture bytes and modes; include file/directory mtimes for read-only checks."""
    result = {}
    for path in sorted(root.rglob('*')):
        info = path.lstat()
        value = (path.read_bytes() if path.is_file() and not path.is_symlink() else None,
                 info.st_mode & 0o7777, os.readlink(path) if path.is_symlink() else None)
        result[path.relative_to(root).as_posix()] = value + ((info.st_mtime_ns,) if timestamps else ())
    if timestamps:
        result['.'] = (None, root.stat().st_mode & 0o7777, None, root.stat().st_mtime_ns)
    return result


class MigrationTests(unittest.TestCase):
    fixture_file = FIXTURE
    fixture_sha256 = FIXTURE_SHA256
    fixture_kind = 'synthetic'

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.home = self.base / 'home'
        self.home.mkdir()
        stack = self.enterContext(ExitStack())
        stack.enter_context(patch.object(core.Path, 'home', return_value=self.home))
        stack.enter_context(patch.dict(os.environ, {'CODEX_HOME': str(self.base / 'codex')}))
        stack.enter_context(patch.object(core, 'CORE', FUTURE_CORE))
        self.fixture = json.loads(self.fixture_file.read_text())
        self.source = self.base / 'future'
        for name in FUTURE_CORE + sum(EXTRAS.values(), ()):
            skill = self.source / 'skills' / name
            skill.mkdir(parents=True)
            (skill / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Future test payload.\n---\nUpdated payload.\n')
        templates = self.source / 'templates'
        templates.mkdir()
        (templates / 'AGENTS.cdf-block.md').write_bytes(core.START + b'\nFuture policy.\n' + core.END + b'\n')
        for name in ('cdf_reviewer', 'cdf_diagnostician'):
            (templates / f'{name}.toml').write_text(f'name = "{name}"\ndescription = "Future role"\ndeveloper_instructions = "Read-only review"\n')
        (self.source / 'subskills.catalog.json').write_text('{"candidates": {}}\n')
        # Synthetic forward version; the repository's release version is untouched.
        (self.source / 'pyproject.toml').write_text('[project]\nversion = "1.2.0.dev0"\n')
        self.number = 0

    def restore(self, scope):
        self.number += 1
        target = self.base / f'{scope}-{self.number}'
        target.mkdir()
        for name, value in self.fixture['snapshots'][scope].items():
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value['text'].encode())
            path.chmod(value['mode'])
        return target

    def action(self, target, scope, action, **kwargs):
        return core.perform(target, scope, action, src=self.source, **kwargs)

    def cli(self, target, scope, action, *arguments):
        # Exercise the actual CLI with the same future inventory/source seam as
        # the in-process tests. Do not edit live HOME or the production registry.
        runner = (
            'import functools, json, runpy, sys; from pathlib import Path; '
            'from unittest.mock import patch; '
            'sys.path.insert(0, sys.argv.pop(1)); '
            'from cdf_installer import core; '
            'core.CORE = tuple(json.loads(sys.argv.pop(1))); '
            'core.perform = functools.partial(core.perform, src=Path(sys.argv.pop(1))); '
            'patch.object(Path, "home", return_value=Path(sys.argv.pop(1))).start(); '
            'script = sys.argv.pop(1); runpy.run_path(script, run_name="__main__")'
        )
        args = [sys.executable, '-c', runner, str(ROOT), json.dumps(FUTURE_CORE),
                str(self.source), str(self.home), str(ROOT / 'scripts/cdf.py'), action,
                '--target', str(target), '--scope', scope, '--json', *arguments]
        if scope == 'global':
            args.extend(('--home', str(target)))
        return subprocess.run(args, text=True, capture_output=True, timeout=30)

    def assert_refused_unchanged(self, target, scope, code, action='upgrade'):
        before = snapshot(target, timestamps=True)
        for dry in (True, False):
            with self.assertRaises(core.CDFError) as caught:
                self.action(target, scope, action, dry=dry)
            self.assertEqual(caught.exception.code, code)
            self.assertEqual(snapshot(target, timestamps=True), before)

    def test_fixture_is_frozen_and_matches_known_inventory(self):
        self.assertEqual(hashlib.sha256(self.fixture_file.read_bytes()).hexdigest(), self.fixture_sha256)
        self.assertIn(self.fixture_kind, self.fixture['kind'])
        self.assertEqual(tuple(self.fixture['core']), LEGACY_CORE_11)
        self.assertEqual(len(self.fixture['core']), 12)
        self.assertTrue(set(RETIRED) <= set(self.fixture['core']))

    def test_m01_m02_legacy_status_through_future_cli(self):
        for scope in ('project', 'global'):
            with self.subTest(scope=scope):
                target = self.restore(scope)
                before = snapshot(target, timestamps=True)
                result = self.cli(target, scope, 'status')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                status = json.loads(result.stdout)
                self.assertEqual((status['state'], status['files'], status['managed_block']),
                                 ('installed', 'clean', 'clean'))
                self.assertEqual(status['skills_discovery'], 'unverified')
                self.assertEqual(snapshot(target, timestamps=True), before)

    def test_m03_m04_m05_m08_m17_upgrade_and_uninstall_both_scopes(self):
        for scope in ('project', 'global'):
            with self.subTest(scope=scope):
                target = self.restore(scope)
                agents = target / ('.codex/AGENTS.md' if scope == 'global' else 'AGENTS.md')
                original = agents.read_bytes()
                start, end = core.block_span(original)
                outside = original[:start] + original[end:]
                user_note = target / '.agents/skills/cdf-planning/user-note.txt'
                user_note.write_bytes(b'Keep my note.\x00\xff')
                before = snapshot(target, timestamps=True)
                preview = self.cli(target, scope, 'upgrade', '--dry-run')
                self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
                plan = json.loads(preview.stdout)
                actions = {op['path']: op['operation'] for op in plan['planned_actions']}
                self.assertEqual(actions['.agents/skills/cdf/SKILL.md'], 'add')
                for name in RETIRED:
                    self.assertEqual(actions[f'.agents/skills/{name}/SKILL.md'], 'remove')
                self.assertEqual(snapshot(target, timestamps=True), before)
                applied = self.cli(target, scope, 'upgrade')
                self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
                manifest = core.manifest_read(target, scope)
                self.assertEqual(manifest['selected_extras'], ['learning', 'operator'])
                names = {p.split('/')[2] for p in manifest['owned_files'] if p.startswith('.agents/skills/')}
                if core.bundle_layout(self.source) == 'single':
                    self.assertEqual(names, {'cdf'})
                    self.assertEqual(manifest['layout'], 'single')
                    modules = set(FUTURE_CORE) - {'cdf'} | set(sum(EXTRAS.values(), ()))
                    actual = {p.split('/')[4] for p in manifest['owned_files']
                              if p.startswith('.agents/skills/cdf/modules/') and p.endswith('/GUIDE.md')}
                    self.assertEqual(actual, modules)
                    self.assertEqual(len(actual), 12)
                    for name in modules:
                        self.assertFalse((target / f'.agents/skills/{name}/SKILL.md').exists())
                        self.assertTrue((target / f'.agents/skills/cdf/modules/{name}/GUIDE.md').is_file())
                else:
                    self.assertEqual(names, set(FUTURE_CORE) | set(sum(EXTRAS.values(), ())))
                    self.assertEqual(len(names), 13)
                self.assertEqual(core.status(target, scope)['files'], 'clean')
                for name in RETIRED:
                    self.assertFalse((target / f'.agents/skills/{name}/SKILL.md').exists())
                content = agents.read_bytes()
                start, end = core.block_span(content)
                self.assertEqual(content[:start] + content[end:], outside)
                self.assertEqual(self.action(target, scope, 'uninstall')['state'], 'absent')
                self.assertEqual(agents.read_bytes(), outside)
                self.assertFalse((target / '.agents/skills/cdf').exists())
                self.assertFalse((target / '.agents/skills/cdf-implementation').exists())
                self.assertEqual(user_note.read_bytes(), b'Keep my note.\x00\xff')
                self.assertEqual((target / 'user-data.txt').read_text(), 'Preserve this unowned file.\n')
                self.assertEqual((target / core.IGNORE).read_bytes(), core.IGNORE_BLOCK)

    def test_m05_explicit_extra_revocation(self):
        target = self.restore('project')
        self.action(target, 'project', 'upgrade', disable=('learning',))
        self.assertEqual(core.manifest_read(target, 'project')['selected_extras'], ['operator'])
        self.assertFalse((target / '.agents/skills/cdf-explain/SKILL.md').exists())
        if core.bundle_layout(self.source) == 'single':
            self.assertFalse((target / '.agents/skills/cdf/modules/cdf-explain/GUIDE.md').exists())
            self.assertFalse((target / '.agents/skills/cdf/modules/cdf-teach/GUIDE.md').exists())
            self.assertTrue((target / '.agents/skills/cdf/modules/cdf-model-calibration/GUIDE.md').is_file())
        else:
            self.assertTrue((target / '.agents/skills/cdf-model-calibration/SKILL.md').exists())

    def test_m06_modified_retired_skill_bytes_or_mode_block_upgrade(self):
        for name in RETIRED:
            for change in ('bytes', 'mode'):
                with self.subTest(name=name, change=change):
                    target = self.restore('project')
                    skill = target / f'.agents/skills/{name}/SKILL.md'
                    if change == 'bytes':
                        skill.write_bytes(b'User-authored changes.\xff')
                    else:
                        skill.chmod(0o600)
                    self.assert_refused_unchanged(target, 'project', 'MANAGED_FILE_MODIFIED')

    def test_m07_modified_managed_block_blocks_upgrade(self):
        for scope in ('project', 'global'):
            with self.subTest(scope=scope):
                target = self.restore(scope)
                agents = target / ('.codex/AGENTS.md' if scope == 'global' else 'AGENTS.md')
                agents.write_bytes(agents.read_bytes().replace(core.START + b'\n', core.START + b'\nUser edit.\n'))
                self.assert_refused_unchanged(target, scope, 'MANAGED_FILE_MODIFIED')

    def test_m09_new_skill_and_case_collisions(self):
        for name in ('cdf', 'CDF'):
            with self.subTest(name=name):
                target = self.restore('project')
                path = target / f'.agents/skills/{name}/SKILL.md'
                path.parent.mkdir()
                # The upper-case directory must fail path collision checks even
                # when its skill metadata does not duplicate the desired name.
                declared = 'cdf' if name == 'cdf' else 'user-cdf'
                path.write_text(f'---\nname: {declared}\ndescription: User skill.\n---\n')
                self.assert_refused_unchanged(target, 'project', 'PATH_COLLISION')

    def test_m10_symlink_traversal_and_case_colliding_legacy_paths(self):
        for attack in ('symlink', 'traversal', 'case'):
            with self.subTest(attack=attack):
                target = self.restore('project')
                manifest = target / core.MANIFEST
                value = json.loads(manifest.read_text())
                if attack == 'symlink':
                    path = target / '.agents/skills/cdf-planning/SKILL.md'
                    outside = self.base / 'outside.txt'
                    outside.write_bytes(b'Outside user data.')
                    path.unlink()
                    path.symlink_to(outside)
                else:
                    key = ('../outside.txt' if attack == 'traversal' else
                           '.agents/skills/CDF-planning/SKILL.md')
                    value['owned_files'][key] = {'sha256': 'a' * 64, 'mode': 420}
                    manifest.write_text(json.dumps(value))
                self.assert_refused_unchanged(target, 'project', 'UNSAFE_TARGET' if attack in ('symlink', 'traversal') else 'MANIFEST_UNSUPPORTED')
                if attack == 'symlink':
                    self.assertEqual(outside.read_bytes(), b'Outside user data.')

    def test_m11_invalid_or_mixed_inventory_is_not_legacy_ownership(self):
        for attack in ('header', 'missing', 'unknown', 'mixed', 'partial-mixed', 'extra', 'scope', 'hash', 'mode', 'marker', 'nested'):
            with self.subTest(attack=attack):
                target = self.restore('project')
                manifest = target / core.MANIFEST
                value = json.loads(manifest.read_text())
                if attack == 'header':
                    del value['source_revision']
                elif attack == 'missing':
                    del value['owned_files']['.agents/skills/cdf-backend/SKILL.md']
                elif attack in ('unknown', 'mixed', 'partial-mixed'):
                    name = 'unowned' if attack == 'unknown' else 'cdf'
                    value['owned_files'][f'.agents/skills/{name}/SKILL.md'] = {'sha256': 'a' * 64, 'mode': 420}
                    if attack == 'partial-mixed':
                        value['state'] = 'partial'
                elif attack == 'extra':
                    value['selected_extras'] = []
                elif attack == 'scope':
                    value['scope'] = 'global'
                elif attack in ('hash', 'mode'):
                    value['owned_files']['.agents/skills/cdf-planning/SKILL.md'][
                        'sha256' if attack == 'hash' else 'mode'] = 'bad' if attack == 'hash' else 4096
                elif attack == 'marker':
                    value['managed_blocks']['AGENTS.md']['start_marker'] = 'changed'
                else:
                    value['created_directories'].append('.agents/skills/unowned/nested')
                manifest.write_text(json.dumps(value))
                self.assert_refused_unchanged(target, 'project', 'MANIFEST_UNSUPPORTED')

    def test_m12_crash_before_first_payload_write(self):
        for scope in ('project', 'global'):
            with self.subTest(scope=scope):
                target = self.restore(scope)
                before = snapshot(target)
                with patch.object(core, 'apply_file', side_effect=KeyboardInterrupt('before payload')):
                    with self.assertRaises(KeyboardInterrupt):
                        self.action(target, scope, 'upgrade')
                self.assertEqual(core.status(target, scope)['state'], 'recovery-required')
                self.action(target, scope, 'recover')
                self.assertEqual(snapshot(target), before)

    def test_m13_m14_m15_every_upgrade_replacement_recovers(self):
        for scope in ('project', 'global'):
            baseline = self.restore(scope)
            ops, _, _, _ = core.changes_plan(baseline, scope, 'upgrade', ('learning', 'operator'), self.source)
            replacements = sum(op['operation'] != 'unchanged' for op in ops) + 1
            for failed_index in range(replacements):
                with self.subTest(scope=scope, replacement=failed_index):
                    target = self.base / f'fault-{scope}-{failed_index}'
                    shutil.copytree(baseline, target)
                    before = snapshot(target)
                    calls = 0
                    real_apply = core.apply_file

                    def crash(*args):
                        nonlocal calls
                        real_apply(*args)
                        calls += 1
                        if calls == failed_index + 1:
                            raise KeyboardInterrupt('after replacement')

                    with patch.object(core, 'apply_file', side_effect=crash):
                        with self.assertRaises(KeyboardInterrupt):
                            self.action(target, scope, 'upgrade')
                    self.assertEqual(core.status(target, scope)['state'], 'recovery-required')
                    interrupted = snapshot(target, timestamps=True)
                    self.action(target, scope, 'recover', dry=True)
                    self.assertEqual(snapshot(target, timestamps=True), interrupted)
                    self.assertEqual(self.action(target, scope, 'recover')['state'], 'recovered')
                    self.assertEqual(snapshot(target), before)
                    self.assertEqual(core.status(target, scope)['files'], 'clean')
                    self.assertEqual(self.action(target, scope, 'recover')['state'], 'absent')
                    shutil.rmtree(target)

    def test_m16_legacy_uninstall_without_upgrade_through_future_cli(self):
        for scope in ('project', 'global'):
            with self.subTest(scope=scope):
                target = self.restore(scope)
                before = snapshot(target, timestamps=True)
                preview = self.cli(target, scope, 'uninstall', '--dry-run')
                self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
                self.assertEqual(snapshot(target, timestamps=True), before)
                applied = self.cli(target, scope, 'uninstall')
                self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
                self.assertEqual(json.loads(applied.stdout)['state'], 'absent')
                self.assertFalse((target / '.agents').exists())
                self.assertTrue((target / 'user-data.txt').exists())

    def test_legacy_interrupted_uninstall_journal_survives_registry_change(self):
        for scope in ('project', 'global'):
            with self.subTest(scope=scope):
                target = self.restore(scope)
                before = snapshot(target)
                real_apply = core.apply_file

                def crash(*args):
                    real_apply(*args)
                    raise KeyboardInterrupt('legacy uninstall interrupted')

                with patch.object(core, 'CORE', LEGACY_CORE_11), patch.object(core, 'apply_file', side_effect=crash):
                    with self.assertRaises(KeyboardInterrupt):
                        self.action(target, scope, 'uninstall')
                self.assertEqual(self.action(target, scope, 'recover')['state'], 'recovered')
                self.assertEqual(snapshot(target), before)
                self.assertEqual(core.status(target, scope)['files'], 'clean')

    def test_committed_upgrade_recovery_keeps_new_inventory(self):
        for scope in ('project', 'global'):
            with self.subTest(scope=scope):
                target = self.restore(scope)
                real_unlink = Path.unlink

                def crash(path, *args, **kwargs):
                    if path == target / core.TX / 'journal.json':
                        raise KeyboardInterrupt('committed before journal removal')
                    return real_unlink(path, *args, **kwargs)

                with patch.object(Path, 'unlink', crash):
                    with self.assertRaises(KeyboardInterrupt):
                        self.action(target, scope, 'upgrade')
                self.assertEqual(core.journal_read(target, scope)['phase'], 'complete')
                self.assertEqual(self.action(target, scope, 'recover')['state'], 'recovered')
                manifest = core.manifest_read(target, scope)
                self.assertEqual(manifest['framework_version'], core._version(self.source))
                self.assertIn('.agents/skills/cdf/SKILL.md', manifest['owned_files'])
                self.assertEqual(core.status(target, scope)['files'], 'clean')
                self.assertEqual(self.action(target, scope, 'uninstall')['state'], 'absent')
                self.assertFalse((target / '.agents').exists())

    def test_m18_legacy_modified_skills_partial_then_release(self):
        for scope in ('project', 'global'):
            for upgraded in (False, True):
                with self.subTest(scope=scope, upgraded=upgraded):
                    target = self.restore(scope)
                    if upgraded:
                        self.action(target, scope, 'upgrade')
                    name = 'cdf' if upgraded else 'cdf-planning'
                    skill = target / f'.agents/skills/{name}/SKILL.md'
                    skill.write_text('User skill changes.')
                    self.assertEqual(self.action(target, scope, 'uninstall')['state'], 'partial')
                    self.assertEqual(core.status(target, scope)['state'], 'partial')
                    self.assertEqual(self.action(target, scope, 'uninstall', release_modified_skills=True)['state'], 'absent')
                    self.assertEqual(skill.read_text(), 'User skill changes.')
                    self.assertFalse((target / core.MANIFEST).exists())
        target = self.restore('project')
        with self.assertRaises(core.CDFError) as caught:
            self.action(target, 'project', 'upgrade', release_modified_skills=True)
        self.assertEqual(caught.exception.code, 'INVALID_REQUEST')

    def test_m19_lock_and_recovery_concurrent_edit(self):
        target = self.restore('project')
        with core.Lock(target):
            self.assert_refused_unchanged(target, 'project', 'CONCURRENT_MUTATION')
        real_apply = core.apply_file

        def crash(*args):
            real_apply(*args)
            raise KeyboardInterrupt('after first write')

        with patch.object(core, 'apply_file', side_effect=crash):
            with self.assertRaises(KeyboardInterrupt):
                self.action(target, 'project', 'upgrade')
        self.assert_refused_unchanged(target, 'project', 'RECOVERY_REQUIRED')
        journal = core.journal_read(target, 'project')
        changed = target / journal['paths'][0]['relative_path']
        changed.write_bytes(b'Concurrent user change.')
        self.assert_refused_unchanged(target, 'project', 'CONCURRENT_MUTATION', action='recover')

    def test_m20_downgrade_and_development_release_ordering(self):
        target = self.restore('project')
        for version in ('1.0.0', '1.1.0.dev0'):
            with self.subTest(version=version):
                (self.source / 'pyproject.toml').write_text(f'[project]\nversion = "{version}"\n')
                self.assert_refused_unchanged(target, 'project', 'MANIFEST_UNSUPPORTED')
        versions = ('1.1.0.dev0', '1.1.0-a1', '1.1.0-b1', '1.1.0-rc1', '1.1.0', '1.2.0.dev0')
        self.assertEqual(sorted(versions, key=core._version_key), list(versions))


class RealBundleMigrationTests(MigrationTests):
    """Repeat the matrix with actual G3 payloads and a temporary forward version."""

    def setUp(self):
        self.assertEqual(core.CORE, FUTURE_CORE)
        super().setUp()
        shutil.rmtree(self.source)
        self.source.mkdir()
        for name in ('skills', 'templates'):
            shutil.copytree(ROOT / name, self.source / name)
        shutil.copyfile(ROOT / 'subskills.catalog.json', self.source / 'subskills.catalog.json')
        (self.source / 'pyproject.toml').write_text('[project]\nversion = "1.2.0.dev0"\n')

    def test_actual_source_obeys_recorded_version_ordering(self):
        target = self.restore('project')
        before = snapshot(target, timestamps=True)
        recorded = core.manifest_read(target, 'project')['framework_version']
        if core._version_key(core._version(ROOT)) < core._version_key(recorded):
            with self.assertRaises(core.CDFError) as caught:
                core.perform(target, 'project', 'upgrade', src=ROOT)
            self.assertEqual(caught.exception.code, 'MANIFEST_UNSUPPORTED')
            self.assertEqual(snapshot(target, timestamps=True), before)
        else:
            self.assertEqual(core.perform(target, 'project', 'upgrade', src=ROOT)['state'], 'installed')
            self.assertEqual(core.manifest_read(target, 'project')['framework_version'], core._version(ROOT))

    def test_actual_source_upgrades_equal_version_legacy_shape(self):
        target = self.restore('project')
        manifest = target / core.MANIFEST
        value = json.loads(manifest.read_text())
        value['framework_version'] = core._version(ROOT)
        manifest.write_text(json.dumps(value))
        self.assertEqual(core.perform(target, 'project', 'upgrade', src=ROOT)['state'], 'installed')
        self.assertEqual(core.status(target, 'project')['files'], 'clean')
        self.assertIn('.agents/skills/cdf/SKILL.md', core.manifest_read(target, 'project')['owned_files'])


class PinnedLegacyMigrationTests(RealBundleMigrationTests):
    """Run the lifecycle matrix against an actual recorded 1.1.0 installation."""

    fixture_file = ROOT / 'tests/fixtures/legacy-cdf-11-pinned.json'
    fixture_sha256 = '0c8bdc657b9f39f532ae0e240ef5c4e6b7c420afbda6fac96a5346d0d526b3bf'
    fixture_kind = 'pinned repository'

    def setUp(self):
        super().setUp()
        # Test the source that will be merged, including its release
        # version, rather than the synthetic forward-version source.
        shutil.copyfile(ROOT / 'pyproject.toml', self.source / 'pyproject.toml')



if __name__ == '__main__':
    unittest.main()
