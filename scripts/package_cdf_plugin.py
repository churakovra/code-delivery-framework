#!/usr/bin/env python3
"""Build a portable or opt-in desktop CDF plugin; never register or install it."""
from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cdf_installer import core
from cdf_installer.packaging import PREFIX
from cdf_registry import CORE, EXTRAS


def build_plugin(output, extras=(), root=ROOT, profile="portable"):
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists; choose a new directory')
    if not output.parent.is_dir():
        raise ValueError('Output parent must be an existing directory')
    if profile not in ('portable', 'desktop-controlled'):
        raise ValueError('Unknown plugin profile; choose portable or desktop-controlled')
    files, _ = core.bundle(root, extras, standalone=True)
    selected = set(CORE) | {name for extra in extras for name in EXTRAS[extra]}
    manifest = json.loads((root / 'templates/cdf-plugin.json').read_text())
    manifest['version'] = core._version(root)
    extension = manifest.get('extensions', {}).get('com.openai', {})
    if 'hooks' in extension:
        raise ValueError('Portable profile cannot include lifecycle hooks')
    if profile == 'desktop-controlled':
        manifest['name'] += '-desktop'
        extension['hooks'] = './hooks/hooks.json'
        extension['interface']['longDescription'] = 'CDF skills with optional local metadata hooks. Hooks require native trust review. No enforcement or automatic agent installation.'
    with tempfile.TemporaryDirectory() as folder:
        stage = Path(folder)
        for path, contents in files.items():
            if not path.startswith(PREFIX):
                continue
            destination = stage / 'skills' / path[len(PREFIX):]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(contents)
        (stage / 'skills/cdf/subskills.catalog.json').write_bytes(files['.codex/cdf/subskills.catalog.json'])
        entries = {p.relative_to(stage / 'skills').as_posix() for p in (stage / 'skills').rglob('SKILL.md')}
        if entries != {name + '/SKILL.md' for name in selected}:
            raise ValueError('Unexpected nested or missing native skills')
        for name in selected:
            core.parse_skill(stage / 'skills' / name / 'SKILL.md', name)
        if profile == 'desktop-controlled':
            (stage / 'hooks').mkdir()
            for name in ('hooks.json', 'observe.py'):
                shutil.copyfile(root / 'hooks' / name, stage / 'hooks' / name)
        (stage / 'assets').mkdir()
        shutil.copyfile(root / 'skills/cdf/assets/icon.png', stage / 'assets/icon.png')
        for key in ('composerIcon', 'logo'):
            reference = extension.get('interface', {}).get(key)
            if not isinstance(reference, str) or not reference.startswith('./'):
                raise ValueError('Plugin assets must use ./ relative paths')
            relative = core.relative_path(reference[2:])
            if not (stage / relative).is_file():
                raise ValueError('Plugin asset reference is missing')
        if profile == 'desktop-controlled':
            # This native client discovers bundled hooks through its compatibility
            # manifest, but ignores them in root plugin.json on the tested native client.
            (stage / '.codex-plugin').mkdir()
            legacy = {key: manifest[key] for key in ('name', 'version', 'description')}
            legacy.update(skills='./skills', hooks='./hooks/hooks.json', interface=extension['interface'])
            (stage / '.codex-plugin/plugin.json').write_text(json.dumps(legacy, indent=2) + '\n')
        else:
            (stage / 'plugin.json').write_text(json.dumps(manifest, indent=2) + '\n')
        # copytree refuses an existing output, including one created after preflight.
        shutil.copytree(stage, output)
    return {'state': 'packaged', 'output': str(output), 'version': manifest['version'],
            'profile': profile, 'visible_skills': len(selected),
            'selected_extras': sorted(extras), 'installed': False,
            'skill_sha256': {name: hashlib.sha256((output / 'skills' / name / 'SKILL.md').read_bytes()).hexdigest()
                             for name in sorted(selected)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('portable', 'desktop-controlled'), default='portable')
    parser.add_argument('--output', required=True, help='New plugin directory in an existing parent')
    parser.add_argument('--with-learning', action='store_true')
    parser.add_argument('--with-operator', action='store_true')
    args = parser.parse_args()
    extras = [name for name in ('learning', 'operator') if getattr(args, 'with_' + name)]
    try:
        result = build_plugin(args.output, extras, profile=args.profile)
    except (OSError, ValueError, core.CDFError) as exc:
        print(json.dumps({'state': 'error', 'message': str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
