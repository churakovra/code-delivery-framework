#!/usr/bin/env python3
"""Install and maintain CDF without network or model calls.

For global scope, --target must equal the current home directory. Supply
--home with --target to select a different, explicitly named home (for example,
a disposable home in tests). Project scope cannot target the current home.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cdf_installer import core


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise core.CDFError('INVALID_REQUEST', message)


def parser():
    p = Parser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True, parser_class=Parser)
    validate = sub.add_parser('validate')
    validate.add_argument('--offline', action='store_true')
    validate.add_argument('--runtime', action='store_true')
    validate.add_argument('--json', action='store_true')
    for action in ('install', 'upgrade', 'status', 'uninstall', 'recover', 'doctor'):
        q = sub.add_parser(action)
        q.add_argument('--target', required=True)
        q.add_argument('--scope', choices=('project', 'global'), default='project')
        q.add_argument('--home', help='Selected home for an isolated global installation')
        q.add_argument('--json', action='store_true')
        if action in ('install', 'upgrade', 'uninstall', 'recover'):
            q.add_argument('--dry-run', action='store_true')
        if action == 'uninstall':
            q.add_argument('--release-modified-skills', action='store_true', help='Preserve modified skill files and release their ownership')
        if action in ('install', 'upgrade'):
            for extra in ('learning', 'operator'):
                g = q.add_mutually_exclusive_group()
                g.add_argument('--with-' + extra, action='store_true')
                if action == 'upgrade': g.add_argument('--without-' + extra, action='store_true')
    i = sub.add_parser('integrations')
    nested = i.add_subparsers(dest='integration_action', required=True, parser_class=Parser)
    for name in ('list', 'plan'):
        q = nested.add_parser(name)
        if name == 'plan': q.add_argument('id')
        q.add_argument('--json', action='store_true')
    return p


def run(args):
    if args.action == 'validate':
        core.bundle(extras=('learning', 'operator'))
        try:
            from scripts.validate_cdf import validate_source
            validated = validate_source()
        except (OSError, ValueError, KeyError, ImportError) as exc:
            raise core.CDFError('INVALID_BUNDLE', f'Source contract validation failed: {exc}') from exc
        version = core._version(core.ROOT)
        result = {'schema': 1, 'state': 'valid', 'version': version, 'skills': validated['core_skills'] + validated['optional_skills'], 'network': 'not_used', 'runtime': 'unverified', 'source_contracts': validated}
        if args.runtime:
            executable = shutil.which('codex')
            if not executable:
                raise core.CDFError('RUNTIME_UNAVAILABLE', 'Codex executable not available.', exit_code=4)
            try:
                p = subprocess.run([executable, '--version'], text=True, capture_output=True, timeout=10, check=True)
            except (subprocess.SubprocessError, OSError) as exc:
                raise core.CDFError('RUNTIME_UNAVAILABLE', f'Codex version probe unavailable: {exc}', exit_code=4) from exc
            result['runtime'] = {'version_observed': p.stdout.strip(), 'skill_discovery': 'unverified', 'agent_schema': 'unverified'}
        return result
    if args.action == 'integrations':
        catalog = json.loads((core.ROOT / 'subskills.catalog.json').read_text())
        if args.integration_action == 'list': return {'schema': 1, 'integrations': ['codebase-memory-mcp'], 'state': 'informational'}
        if args.id != 'codebase-memory-mcp': raise core.CDFError('INVALID_REQUEST', 'Unknown integration.', [args.id])
        entry = catalog['candidates'][args.id]
        return {'schema': 1, 'state': 'informational', 'id': args.id, 'source_url': entry['source_url'], 'revision': entry['revision'], 'license_note': entry['license_note'], 'next_action': 'Review source, license, runtime compatibility and installation permissions; no installation was performed.'}
    if args.home and args.scope != 'global':
        raise core.CDFError('INVALID_REQUEST', '--home is only valid with global scope.')
    root = core.target_root(args.target, args.scope, args.home)
    if args.action == 'status': return core.status(root, args.scope)
    if args.action == 'doctor':
        result = core.status(root, args.scope)
        executable = shutil.which('codex')
        result['binary_available'] = bool(executable)
        result['version_observed'] = None
        if executable:
            try:
                observed = subprocess.run([executable, '--version'], text=True, capture_output=True, timeout=10, check=True)
                result['version_observed'] = observed.stdout.strip() or None
            except (subprocess.SubprocessError, OSError):
                pass
        result['agent_schema_supported'] = 'unverified'
        return result
    enabled = [n for n in ('learning', 'operator') if getattr(args, 'with_' + n, False)]
    disabled = [n for n in ('learning', 'operator') if getattr(args, 'without_' + n, False)]
    return core.perform(root, args.scope, args.action, dry=args.dry_run, enable=enabled, disable=disabled, release_modified_skills=getattr(args, 'release_modified_skills', False))


def main(argv=None):
    args = None
    try:
        args = parser().parse_args(argv)
        result = run(args)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except core.CDFError as exc:
        conflicts = {'PATH_COLLISION', 'MANAGED_FILE_MODIFIED', 'MANAGED_BLOCK_MODIFIED',
                     'MANIFEST_UNSUPPORTED', 'RECOVERY_REQUIRED',
                     'CONCURRENT_MUTATION'}
        if (args is not None and getattr(args, 'dry_run', False)
                and args.action in ('install', 'upgrade', 'uninstall', 'recover')
                and exc.code in conflicts):
            print(json.dumps({'schema': 1, 'action': args.action, 'state': 'conflict',
                              'scope': args.scope, 'target': str(Path(args.target).expanduser().absolute()),
                              'planned_actions': [], 'conflicts': exc.paths or [str(exc)],
                              'warnings': [f'{exc.code}: {exc}']}, sort_keys=True))
            return 3 if args.action == 'recover' and exc.exit_code == 3 else 2
        print(json.dumps({'schema': 1, 'state': 'error', 'code': exc.code, 'message': str(exc), 'affected_paths': exc.paths, 'next_action': 'Inspect the reported paths and resolve the condition before retrying.'}, sort_keys=True))
        return exc.exit_code
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({'schema': 1, 'state': 'error', 'code': 'IO_FAILURE', 'message': str(exc), 'affected_paths': [], 'next_action': 'Inspect the filesystem and retry when safe.'}, sort_keys=True))
        return 5


if __name__ == '__main__':
    raise SystemExit(main())
