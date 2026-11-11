"""Run original pinned installers, offline, against temporary homes only."""
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from cdf_installer import core

ROOT = Path(__file__).resolve().parents[1]
PINNED_RELEASES = {
    '1.2.1': '0409be3c724e27efc9f33e6fa93f6259ace2a26e',
    '1.3.0': 'c0c1b72f5f1e6f2b56b86602d0aa12261ce62930',  # User-approved local single-entry baseline, not a published release.
}


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class PinnedReleaseMigrationTests(unittest.TestCase):
    def source(self, revision, destination):
        found = subprocess.run(['git', 'cat-file', '-e', revision + '^{commit}'], cwd=ROOT,
                               capture_output=True, timeout=10)
        if found.returncode:
            self.skipTest('Pinned source history unavailable; fetch full repository history to run this check')
        data = subprocess.check_output([
            'git', 'archive', '--format=tar', revision, 'pyproject.toml', 'cdf_registry.py',
            'cdf_installer', 'cdf_runtime', 'scripts/cdf.py', 'schemas', 'skills', 'templates',
            'subskills.catalog.json'], cwd=ROOT, timeout=15)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            for member in archive:
                relative = PurePosixPath(member.name)
                self.assertFalse(relative.is_absolute() or '..' in relative.parts)
                if member.isdir(): continue
                self.assertTrue(member.isfile(), 'Pinned installer fixture must contain regular files only')
                path = destination / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.extractfile(member).read())
                path.chmod(member.mode)
        return destination

    def test_original_installers_upgrade_both_scopes_and_preserve_user_bytes(self):
        for version, revision in PINNED_RELEASES.items():
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                source = self.source(revision, base / 'source')
                self.assertEqual(core._version(source), version)
                for scope in ('project', 'global'):
                    with self.subTest(scope=scope):
                        home = base / (scope + '-home'); home.mkdir()
                        target = home if scope == 'global' else base / 'project'; target.mkdir(exist_ok=True)
                        agents = target / ('.codex/AGENTS.md' if scope == 'global' else 'AGENTS.md')
                        agents.parent.mkdir(parents=True, exist_ok=True)
                        original = b'User policy: preserve bytes.\r\n'
                        agents.write_bytes(original)
                        env = {'PATH': os.environ.get('PATH', os.defpath), 'HOME': str(home),
                               'CODEX_HOME': str(home / '.codex'), 'PYTHONDONTWRITEBYTECODE': '1'}
                        command = [sys.executable, str(source / 'scripts/cdf.py'), 'install',
                                   '--target', str(target), '--scope', scope, '--with-learning',
                                   '--with-operator', '--json']
                        if scope == 'global': command += ['--home', str(home)]
                        result = subprocess.run(command, env=env, cwd=source, capture_output=True,
                                                text=True, timeout=30)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        (target / 'user-data.txt').write_bytes(b'Unowned data\x00')
                        with patch.object(Path, 'home', return_value=home), patch.dict(os.environ, env):
                            manifest = core.manifest_read(target, scope)
                            self.assertEqual(manifest['framework_version'], version)
                            before = snapshot(target)
                            core.perform(target, scope, 'upgrade', dry=True)
                            self.assertEqual(snapshot(target), before)
                            core.perform(target, scope, 'upgrade')
                            current = core.manifest_read(target, scope)
                            self.assertEqual(current['layout'], 'single')
                            self.assertEqual(current['framework_version'], core._version(ROOT))
                            self.assertEqual(set(current['selected_extras']), {'learning', 'operator'})
                            self.assertEqual(core.status(target, scope)['files'], 'clean')
                            self.assertEqual(len(list((target / '.agents/skills').rglob('SKILL.md'))), 1)
                            core.perform(target, scope, 'uninstall')
                            self.assertEqual(agents.read_bytes(), original)
                            self.assertEqual((target / 'user-data.txt').read_bytes(), b'Unowned data\x00')
                            self.assertFalse((target / core.MANIFEST).exists())
