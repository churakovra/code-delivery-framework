#!/usr/bin/env python3
"""Build the CDF plugin with skills and native context hooks; never install it."""
from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path
import shutil
import sys
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cdf_installer import core
from cdf_installer.packaging import PREFIX
from cdf_registry import CORE, EXTRAS


# These native clients were observed to ignore hooks when root plugin.json is
# present. Keep one identity; target these clients with the supported legacy
# layout, not a second desktop plugin or a second hook registration.
COMPATIBILITY_CLIENTS = {'codex-cli 0.167.0-alpha.4.1', 'codex-cli 0.169.0-alpha.11.1'}


def client_version(binary):
    if binary is None:
        return None
    with tempfile.TemporaryDirectory(prefix='cdf-package-client-') as temporary:
        home = Path(temporary).resolve()
        (home / '.codex').mkdir()
        env = {'HOME': str(home), 'CODEX_HOME': str(home / '.codex'),
               'PATH': os.environ.get('PATH', os.defpath), 'TMPDIR': str(home)}
        try:
            result = subprocess.run([str(binary), '--version'], env=env, cwd=home,
                                    capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError('Could not identify target Codex client') from exc
        if result.returncode or not result.stdout.strip():
            raise ValueError('Could not identify target Codex client')
        return result.stdout.strip()


def build_plugin(output, extras=(), root=ROOT, profile="standard", codex=None):
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists; choose a new directory')
    if not output.parent.is_dir():
        raise ValueError('Output parent must be an existing directory')
    if profile not in ('standard', 'portable', 'desktop-controlled'):
        raise ValueError('Unknown plugin profile; use the standard build (old profile flags are aliases)')
    observed_client = client_version(codex)
    compatibility_only = observed_client in COMPATIBILITY_CLIENTS
    files, _ = core.bundle(root, extras, standalone=True)
    selected = set(CORE) | {name for extra in extras for name in EXTRAS[extra]}
    manifest = json.loads((root / 'templates/cdf-plugin.json').read_text())
    manifest['version'] = core._version(root)
    extension = manifest.get('extensions', {}).get('com.openai', {})
    if manifest.get('name') != 'code-delivery-framework' or extension.get('hooks') != './hooks/hooks.json':
        raise ValueError('CDF requires one plugin identity and one bundled hooks path')
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
        (stage / 'hooks').mkdir()
        for name in ('hooks.json', 'observe.py', 'cdf_context.py'):
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
        if not compatibility_only:
            (stage / 'plugin.json').write_text(json.dumps(manifest, indent=2) + '\n')
        # A fallback, not a second plugin: current hosts select the inline
        # OpenAI extension instead of merging it with this compatibility file.
        (stage / '.codex-plugin').mkdir()
        legacy = {key: manifest[key] for key in ('name', 'version', 'description')}
        legacy.update(skills='./skills', hooks=extension['hooks'], interface=extension['interface'])
        (stage / '.codex-plugin/plugin.json').write_text(json.dumps(legacy, indent=2) + '\n')
        # copytree refuses an existing output, including one created after preflight.
        shutil.copytree(stage, output)
    return {'state': 'packaged', 'output': str(output), 'version': manifest['version'],
            'profile': 'standard', 'client_observed': observed_client,
            'manifest_layout': 'compatibility' if compatibility_only else 'root-with-fallback',
            'visible_skills': len(selected),
            'selected_extras': sorted(extras), 'installed': False,
            'skill_sha256': {name: hashlib.sha256((output / 'skills' / name / 'SKILL.md').read_bytes()).hexdigest()
                             for name in sorted(selected)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('standard', 'portable', 'desktop-controlled'), default='standard',
                        help='Deprecated profile selection; all values build the same CDF plugin')
    parser.add_argument('--codex', type=Path, help='Target native client; defaults to codex on PATH')
    parser.add_argument('--output', required=True, help='New plugin directory in an existing parent')
    parser.add_argument('--with-learning', action='store_true', help='Deprecated compatibility alias; teaching and explanation are standard')
    parser.add_argument('--with-operator', action='store_true')
    args = parser.parse_args()
    extras = [name for name in ('learning', 'operator') if getattr(args, 'with_' + name)]
    try:
        result = build_plugin(args.output, extras, profile=args.profile, codex=args.codex or shutil.which('codex'))
    except (OSError, ValueError, core.CDFError) as exc:
        print(json.dumps({'state': 'error', 'message': str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
