#!/usr/bin/env python3
"""Build a skills-only CDF plugin directory; never register or install it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cdf_installer import core
from cdf_installer.packaging import PREFIX


def build_plugin(output, extras=(), root=ROOT):
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists; choose a new directory')
    if not output.parent.is_dir():
        raise ValueError('Output parent must be an existing directory')
    if core.bundle_layout(root) != 'single':
        raise ValueError('Plugin packaging requires the single-skill layout')
    files, _ = core.bundle(root, extras)
    manifest = json.loads((root / 'templates/cdf-plugin.json').read_text())
    manifest['version'] = core._version(root)
    with tempfile.TemporaryDirectory() as folder:
        stage = Path(folder)
        for path, contents in files.items():
            if not path.startswith(PREFIX):
                continue
            destination = stage / 'skills' / path[len(PREFIX):]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(contents)
        (stage / 'assets').mkdir()
        shutil.copyfile(root / 'assets/icon.png', stage / 'assets/icon.png')
        (stage / 'plugin.json').write_text(json.dumps(manifest, indent=2) + '\n')
        # copytree refuses an existing output, including one created after preflight.
        shutil.copytree(stage, output)
    return {'state': 'packaged', 'output': str(output), 'version': manifest['version'],
            'visible_skills': 1, 'selected_extras': sorted(extras), 'installed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New plugin directory in an existing parent')
    parser.add_argument('--with-learning', action='store_true')
    parser.add_argument('--with-operator', action='store_true')
    args = parser.parse_args()
    extras = [name for name in ('learning', 'operator') if getattr(args, 'with_' + name)]
    try:
        result = build_plugin(args.output, extras)
    except (OSError, ValueError, core.CDFError) as exc:
        print(json.dumps({'state': 'error', 'message': str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
