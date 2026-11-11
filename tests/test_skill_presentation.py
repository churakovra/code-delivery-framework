"""Check presentation assets at the installation boundary, without a live host."""
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import tomllib
import unittest
import xml.etree.ElementTree as ET

from scripts.package_cdf_plugin import build_plugin

ROOT = Path(__file__).resolve().parents[1]


class SkillPresentationTests(unittest.TestCase):
    def test_local_install_preserves_kernel_presentation_and_explicit_operator_routing(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder).resolve()
            result = subprocess.run(
                [sys.executable, str(ROOT / 'scripts/cdf.py'), 'install',
                 '--target', str(target), '--scope', 'global', '--home', str(target), '--with-learning', '--with-operator', '--json'],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for name in ('cdf',):
                source = ROOT / 'skills' / name
                installed = target / '.agents/skills' / name
                metadata = installed / 'agents/openai.yaml'
                self.assertEqual(metadata.read_bytes(), (source / 'agents/openai.yaml').read_bytes())
                fields = {key: json.loads(value) for key, value in re.findall(
                    r'^  (\w+): (".*")$', metadata.read_text(), re.M)}
                self.assertTrue(fields['display_name'].startswith('CDF'))
                self.assertTrue(25 <= len(fields['short_description']) <= 64)
                for key in ('icon_small', 'icon_large'):
                    relative = Path(fields[key])
                    self.assertFalse(relative.is_absolute())
                    self.assertNotIn('..', relative.parts)
                    icon = installed / relative
                    self.assertEqual(icon.read_bytes(), (source / relative).read_bytes())
                    if icon.suffix == '.svg':
                        self.assertEqual(ET.parse(icon).getroot().tag, '{http://www.w3.org/2000/svg}svg')
                        self.assertNotIn('rx="14"', icon.read_text())
                    else:
                        self.assertEqual(icon.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')
                        self.assertEqual(struct.unpack('>II', icon.read_bytes()[16:24]), (256, 256))
            self.assertFalse(list((installed / 'modules').rglob('openai.yaml')))
            self.assertFalse(list((installed / 'modules').rglob('icon.*')))
            self.assertIn('Read it only when the user explicitly requests it.',
                          (installed / 'modules/index.md').read_text())
            self.assertIn('Read this module only for an explicit user request',
                          (installed / 'modules/cdf-model-calibration/GUIDE.md').read_text())

    def test_plugin_identity_version_and_assets(self):
        self.assertNotIn('version', json.loads((ROOT / 'templates/cdf-plugin.json').read_text()))
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'plugin'
            build_plugin(output)
            manifest = json.loads((output / 'plugin.json').read_text())
            packaged_icon = (output / 'assets/icon.png').read_bytes()
        version = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']['version']
        self.assertEqual(manifest['version'], version)
        self.assertEqual(manifest['name'], 'code-delivery-framework')
        interface = manifest['extensions']['com.openai']['interface']
        self.assertEqual(interface['displayName'], 'Code Delivery Framework')
        self.assertLessEqual(len(interface['shortDescription']), 30)
        for key in ('composerIcon', 'logo'):
            self.assertTrue(interface[key].startswith('./assets/'))
            self.assertEqual(packaged_icon[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(packaged_icon, (ROOT / 'skills/cdf/assets/icon.png').read_bytes())
        # No unexpected tool connections or hooks in the skills-only package.
        self.assertEqual(set(manifest['extensions']['com.openai']), {'interface'})


if __name__ == '__main__':
    unittest.main()
