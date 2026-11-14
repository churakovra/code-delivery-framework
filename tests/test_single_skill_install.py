"""Exercise single-entry packaging and recoverable migration in isolated targets."""
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

from cdf_installer import core
from cdf_registry import CORE, EXTRAS
from scripts.package_cdf_plugin import build_plugin

ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mode)
            for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


class SingleSkillTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.home = self.base / 'home'; self.home.mkdir()
        self.target = self.base / 'project'; self.target.mkdir()
        home_patch = patch.object(Path, 'home', return_value=self.home)
        home_patch.start(); self.addCleanup(home_patch.stop)
        env_patch = patch.dict(os.environ, {'CODEX_HOME': str(self.base / 'codex')})
        env_patch.start(); self.addCleanup(env_patch.stop)

    def assert_single(self, target, extras=()):
        skills = target / '.agents/skills'
        self.assertEqual([p.relative_to(skills).as_posix() for p in skills.rglob('SKILL.md')], ['cdf/SKILL.md'])
        modules = set(CORE) - {'cdf'}
        for extra in extras: modules.update(EXTRAS[extra])
        self.assertEqual({p.parent.name for p in skills.rglob('GUIDE.md')}, modules)
        kernel = skills / 'cdf/SKILL.md'
        self.assertIn('modules/index.md', kernel.read_text())
        # Verify shipped guidance bytes, not whether a model follows them.
        for name in ('delivery-workflow.md', 'quality-contract.md'):
            self.assertEqual((kernel.parent / 'references' / name).read_bytes(),
                             (ROOT / 'skills/cdf/references' / name).read_bytes())
        source_kernel = (ROOT / 'skills/cdf/SKILL.md').read_text()
        prefix, optional = source_kernel.split('## Optional subskills', 1)
        self.assertTrue(kernel.read_text().startswith(prefix))
        self.assertTrue(kernel.read_text().endswith('## Optional subskills' + optional))
        index = skills / 'cdf/modules/index.md'
        self.assertEqual(set(re.findall(r'\]\(([^)]+)\)', index.read_text())),
                         {f'{name}/GUIDE.md' for name in modules})
        for relative in re.findall(r'\]\(([^)]+)\)', index.read_text()):
            guide = index.parent / relative
            self.assertTrue(guide.is_file())
            for ref in re.findall(r'`(references/[^`]+\.md)`', guide.read_text()):
                self.assertTrue((guide.parent / ref).is_file(), ref)
        catalog = json.loads((skills / 'cdf/subskills.catalog.json').read_text())
        self.assertIn('candidates', catalog)
        self.assertIn('Model calibration is never selected implicitly.', index.read_text())
        self.assertEqual(core.status(target, 'global' if target == self.home else 'project')['files'], 'clean')

    def flat_source(self):
        source = self.base / 'old-source'; source.mkdir()
        for name in ('skills', 'templates'):
            shutil.copytree(ROOT / name, source / name)
        shutil.copyfile(ROOT / 'subskills.catalog.json', source / 'subskills.catalog.json')
        (source / 'pyproject.toml').write_text('[project]\nversion = "1.2.1"\n')
        return source

    def test_fresh_project_and_global_install_extras_upgrade_and_uninstall(self):
        for scope, target in [('project', self.target), ('global', self.home)]:
            with self.subTest(scope=scope):
                agents = target / ('.codex/AGENTS.md' if scope == 'global' else 'AGENTS.md')
                agents.parent.mkdir(parents=True, exist_ok=True)
                agents.write_bytes(b'User instructions without newline')
                original = agents.read_bytes()
                before = snapshot(target)
                core.perform(target, scope, 'install', dry=True)
                self.assertEqual(snapshot(target), before)
                core.perform(target, scope, 'install', enable=('learning', 'operator'))
                self.assert_single(target, ('learning', 'operator'))
                m = core.manifest_read(target, scope)
                self.assertEqual(m['layout'], 'single')
                core.perform(target, scope, 'upgrade', disable=('learning',))
                self.assert_single(target, ('operator',))
                core.perform(target, scope, 'uninstall')
                self.assertEqual(agents.read_bytes(), original)
                self.assertFalse((target / '.agents/skills/cdf').exists())

    def test_flat_upgrade_preserves_extras_user_files_and_removes_old_entries(self):
        old = self.flat_source()
        for scope, target in [('project', self.target), ('global', self.home)]:
            with self.subTest(scope=scope):
                core.perform(target, scope, 'install', src=old, enable=('learning', 'operator'))
                user_file = target / '.agents/skills/cdf-debugging/notes.txt'
                user_file.write_bytes(b'User note')
                core.perform(target, scope, 'upgrade')
                self.assert_single(target, ('learning', 'operator'))
                self.assertEqual(user_file.read_bytes(), b'User note')
                self.assertFalse((user_file.parent / 'SKILL.md').exists())

    def test_edited_flat_skill_blocks_migration_without_writes(self):
        core.perform(self.target, 'project', 'install', src=self.flat_source())
        file = self.target / '.agents/skills/cdf-debugging/SKILL.md'
        file.write_bytes(file.read_bytes() + b'User changes')
        before = snapshot(self.target)
        with self.assertRaises(core.CDFError) as caught:
            core.perform(self.target, 'project', 'upgrade')
        self.assertEqual(caught.exception.code, 'MANAGED_FILE_MODIFIED')
        self.assertEqual(snapshot(self.target), before)

    def test_interrupted_flat_migration_restores_original_payload(self):
        core.perform(self.target, 'project', 'install', src=self.flat_source())
        before = snapshot(self.target)
        apply_file = core.apply_file
        writes = 0
        def crash(*args, **kwargs):
            nonlocal writes
            apply_file(*args, **kwargs)
            writes += 1
            if writes == 7: raise KeyboardInterrupt('simulated power loss')
        with patch.object(core, 'apply_file', side_effect=crash):
            with self.assertRaises(KeyboardInterrupt): core.perform(self.target, 'project', 'upgrade')
        self.assertEqual(core.status(self.target, 'project')['state'], 'recovery-required')
        self.assertEqual(core.perform(self.target, 'project', 'recover')['state'], 'recovered')
        self.assertEqual(snapshot(self.target), before)
        core.perform(self.target, 'project', 'upgrade')
        self.assert_single(self.target)

    def test_edited_module_blocks_upgrade_and_can_release_whole_cdf_folder(self):
        core.perform(self.target, 'project', 'install')
        guide = self.target / '.agents/skills/cdf/modules/cdf-debugging/GUIDE.md'
        guide.write_bytes(guide.read_bytes() + b'User module edits')
        before = snapshot(self.target)
        with self.assertRaises(core.CDFError) as caught:
            core.perform(self.target, 'project', 'upgrade')
        self.assertEqual(caught.exception.code, 'MANAGED_FILE_MODIFIED')
        self.assertEqual(snapshot(self.target), before)
        cdf = self.target / '.agents/skills/cdf'
        preserved = snapshot(cdf)
        result = core.perform(self.target, 'project', 'uninstall', release_modified_skills=True)
        self.assertEqual(result['state'], 'absent')
        self.assertEqual(snapshot(cdf), preserved)
        self.assertFalse((self.target / core.MANIFEST).exists())

    def test_single_manifest_rejects_missing_modules_and_undeclared_extras(self):
        core.perform(self.target, 'project', 'install')
        path = self.target / core.MANIFEST
        original = path.read_bytes()
        for mode in ('missing', 'extra', 'nested-skill', 'layout'):
            with self.subTest(mode=mode):
                m = json.loads(original)
                if mode == 'missing': del m['owned_files']['.agents/skills/cdf/modules/cdf-debugging/GUIDE.md']
                if mode == 'extra': m['owned_files']['.agents/skills/cdf/modules/cdf-teach/GUIDE.md'] = {'sha256': 'a'*64, 'mode': 420}
                if mode == 'nested-skill': m['owned_files']['.agents/skills/cdf/modules/cdf-debugging/SKILL.md'] = {'sha256': 'a'*64, 'mode': 420}
                if mode == 'layout': m['layout'] = 'unknown'
                path.write_text(json.dumps(m))
                with self.assertRaises(core.CDFError): core.manifest_read(self.target, 'project')
        path.write_bytes(original)

    def test_portable_plugin_omits_disabled_extras_and_rejects_nested_skills(self):
        output = self.base / 'default-plugin'
        result = build_plugin(output)
        self.assertEqual({p.parent.name for p in output.rglob('SKILL.md')}, set(CORE))
        self.assertEqual(result['visible_skills'], len(CORE))
        self.assertFalse((output / 'skills/cdf/modules').exists())
        for name in CORE:
            self.assertEqual((output / 'skills' / name / 'SKILL.md').read_bytes(),
                             (ROOT / 'skills' / name / 'SKILL.md').read_bytes())
        files, block = core.bundle(standalone=True)
        files['.agents/skills/cdf/references/accidental/SKILL.md'] = b'---\nname: accidental\ndescription: Bad nesting.\n---\n'
        with patch('scripts.package_cdf_plugin.core.bundle', return_value=(files, block)):
            with self.assertRaisesRegex(ValueError, 'nested'):
                build_plugin(self.base / 'bad-plugin')
        self.assertFalse((self.base / 'bad-plugin').exists())

    def test_portable_skill_catalog_and_declared_local_references_exist(self):
        import re
        output = self.base / 'portable-links'
        build_plugin(output)
        catalog = output / 'skills/cdf/subskills.catalog.json'
        self.assertTrue(catalog.is_file())
        for skill in (output / 'skills').glob('*/SKILL.md'):
            text = skill.read_text()
            if 'Resolve candidates through the bundled catalog' in text:
                self.assertIn('skills/cdf/subskills.catalog.json', text)
                self.assertTrue(catalog.is_file(), skill)
            for relative in re.findall(r'\]\(([^)#]+\.md)\)', text):
                if relative.startswith(('http:', 'https:')):
                    continue
                self.assertTrue((skill.parent / relative).resolve().is_file(),
                                f'{skill.relative_to(output)} -> {relative}')
        with self.assertRaisesRegex(ValueError, 'portable'):
            build_plugin(self.base / 'unknown-profile', profile='desktop')

    def test_plugin_retains_standalone_source_skills_without_policy_or_native_agents(self):
        output = self.base / 'plugin'
        result = build_plugin(output, ('learning', 'operator'))
        self.assertEqual(result['visible_skills'], len(CORE) + sum(map(len, EXTRAS.values())))
        self.assertEqual({p.parent.name for p in output.rglob('SKILL.md')}, set(CORE) | set(sum(EXTRAS.values(), ())))
        files, _ = core.bundle(extras=('learning', 'operator'), standalone=True)
        for path, contents in files.items():
            if path.startswith('.agents/skills/'):
                self.assertEqual((output / 'skills' / path.removeprefix('.agents/skills/')).read_bytes(), contents)
        self.assertFalse((output / '.codex').exists())
        self.assertFalse((output / 'AGENTS.md').exists())
        before = snapshot(output)
        with self.assertRaises(ValueError): build_plugin(output)
        self.assertEqual(snapshot(output), before)


if __name__ == '__main__':
    unittest.main()
