#!/usr/bin/env python3
"""Probe CDF discovery in a temporary home via app-server; never run a model."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cdf_installer import core
from cdf_runtime.codex import app_server
from cdf_registry import CORE, EXTRAS
from scripts.package_cdf_plugin import build_plugin


def probe(binary, *, plugin=False, extras=None):
    extras = tuple(extras if extras is not None else (() if plugin else ("learning", "operator")))
    with tempfile.TemporaryDirectory(prefix='cdf-discovery-') as temporary:
        base = Path(temporary).resolve()
        home = base / 'home'
        (home / '.codex').mkdir(parents=True)
        target = base / 'project'
        target.mkdir()
        env = {'HOME': str(home), 'CODEX_HOME': str(home / '.codex'),
               'PATH': os.environ.get('PATH', ''), 'TMPDIR': str(base)}
        installation = []
        if plugin:
            marketplace = base / 'marketplace'
            (marketplace / '.agents/plugins').mkdir(parents=True)
            (marketplace / 'plugins').mkdir()
            build_plugin(marketplace / 'plugins/cdf', extras)
            (marketplace / '.agents/plugins/marketplace.json').write_text(json.dumps({
                'name': 'cdf-probe', 'plugins': [{'name': 'code-delivery-framework',
                'source': {'source': 'local', 'path': './plugins/cdf'},
                'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
                'category': 'Developer Tools'}]}))
            for arguments in (['plugin', 'marketplace', 'add', str(marketplace), '--json'],
                              ['plugin', 'add', 'code-delivery-framework@cdf-probe', '--json']):
                result = subprocess.run([str(binary), *arguments], cwd=target, env=env,
                                        capture_output=True, text=True, timeout=20)
                if result.returncode:
                    raise ValueError('Native plugin setup failed: ' + result.stderr[:2000])
                installation.append(json.loads(result.stdout))
        else:
            with patch.object(Path, 'home', return_value=home), patch.dict(os.environ, {'CODEX_HOME': env['CODEX_HOME']}):
                core.perform(target, 'project', 'install', enable=extras)
        with app_server(binary, cwd=target, env=env) as (request, initialized):
            rows = request('skills/list', {'cwds': [str(target)], 'forceReload': True})['data']
            skills = [skill for row in rows for skill in row['skills']
                      if skill['name'] == 'cdf' or skill['name'].startswith(('cdf-', 'code-delivery-framework:', 'code-delivery-framework-desktop:'))]
            local_errors = [error for row in rows for error in row.get('errors', [])]
            expected = {'code-delivery-framework:' + name for name in (set(CORE) | {name for extra in extras for name in EXTRAS[extra]})} if plugin else {'cdf'}
            if len(skills) != len(expected) or {skill['name'] for skill in skills} != expected or local_errors:
                raise ValueError('Unexpected discovery entries or errors: ' + json.dumps({'skills': skills, 'errors': local_errors}))
            if not all(skill.get('enabled') for skill in skills):
                raise ValueError('A CDF skill is disabled')
            kernel = next(skill for skill in skills if skill['name'] == ('code-delivery-framework:cdf' if plugin else 'cdf'))
            interface = kernel.get('interface') or {}
            if not all(Path(interface.get(key, '')).is_file() for key in ('iconSmall', 'iconLarge')):
                raise ValueError('CDF icon paths are unavailable')
            return {'state': 'passed', 'probe': 'skills/list', 'cdf_entries': sorted(expected),
                    'enabled': True, 'small_icon': Path(interface['iconSmall']).suffix,
                    'large_icon': Path(interface['iconLarge']).suffix, 'errors': [],
                    'model_runs': 0, 'home': 'temporary', 'client': initialized.get('userAgent'),
                    'distribution': 'portable-plugin' if plugin else 'legacy-single',
                    'installation': installation, 'skills_response': skills,
                    'method_application': 'NOT_OBSERVED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex', type=Path, required=True, help='Path to a Codex executable supporting app-server')
    parser.add_argument('--plugin-portable', action='store_true', help='Install a portable plugin in a disposable HOME')
    parser.add_argument('--with-learning', action='store_true')
    parser.add_argument('--with-operator', action='store_true')
    args = parser.parse_args()
    try:
        extras = [name for name in ('learning', 'operator') if getattr(args, 'with_' + name)] if args.plugin_portable else None
        result = probe(args.codex.expanduser().resolve(), plugin=args.plugin_portable, extras=extras)
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({'state': 'unavailable', 'message': str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
