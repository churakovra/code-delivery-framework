#!/usr/bin/env python3
"""Validate CDF and manage optional native roles; plugins are installed by Codex itself."""
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
    q = sub.add_parser('doctor')
    q.add_argument('--target', required=True)
    q.add_argument('--scope', choices=('project', 'global'), default='project')
    q.add_argument('--home', help='Selected home for an isolated global inspection')
    q.add_argument('--json', action='store_true')
    q.add_argument('--runtime', action='store_true', help='Read native hook discovery; never enable or trust hooks')
    q.add_argument('--codex', type=Path)
    q.add_argument('--plugin-data', type=Path, help='Explicit desktop plugin data directory; only events.jsonl is read')
    q.add_argument('--session-id', help='Filter selected historical hook records')
    q = sub.add_parser('recover')
    q.add_argument('--target', required=True)
    q.add_argument('--scope', choices=('project', 'global'), default='project')
    q.add_argument('--home', help='Selected home for an isolated recovery target')
    q.add_argument('--dry-run', action='store_true')
    q.add_argument('--json', action='store_true')
    q = sub.add_parser('profile')
    q.add_argument('--target', required=True)
    q.add_argument('--scope', choices=('project', 'global'), default='project')
    q.add_argument('--home', help='Explicit alternative home for isolated global setup')
    q.add_argument('--policy', type=Path, help='Explicit native candidate policy')
    q.add_argument('--profile', choices=('budget', 'balanced', 'quality'))
    q.add_argument('--codex', type=Path, help='Native Codex executable for capability checks')
    q.add_argument('--json', action='store_true')
    q.add_argument('--dry-run', action='store_true', help='Preview only; default when no action is selected')
    choice = q.add_mutually_exclusive_group()
    choice.add_argument('--check', action='store_true', help='Check advertised model/effort support, not effective role execution')
    choice.add_argument('--apply', action='store_true', help='Install native role files after a capability check')
    choice.add_argument('--rollback', action='store_true', help='Remove CDF-created role files; does not restore the previous successful profile')
    i = sub.add_parser('integrations')
    nested = i.add_subparsers(dest='integration_action', required=True, parser_class=Parser)
    for name in ('list', 'plan'):
        q = nested.add_parser(name)
        if name == 'plan': q.add_argument('id')
        q.add_argument('--json', action='store_true')
    return p


def run(args):
    if args.action == 'validate':
        files, _ = core.bundle(extras=('learning', 'operator'), standalone=True)
        try:
            from scripts.validate_cdf import validate_source
            validated = validate_source()
        except (OSError, ValueError, KeyError, ImportError) as exc:
            raise core.CDFError('INVALID_BUNDLE', f'Source contract validation failed: {exc}') from exc
        version = core._version(core.ROOT)
        result = {'schema': 1, 'state': 'valid', 'version': version, 'skills': sum(path.endswith('/SKILL.md') for path in files), 'layout': core.bundle_layout(core.ROOT), 'source_modules': validated['core_skills'] + validated['optional_skills'], 'network': 'not_used', 'runtime': 'unverified', 'source_contracts': validated}
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
    if args.action == 'profile':
        if args.home and args.scope != 'global':
            raise core.CDFError('INVALID_REQUEST', '--home is only valid with global scope.')
        root = core.target_root(args.target, args.scope, args.home)
        from cdf_installer.agents import perform_profile
        from cdf_runtime.policy import native_profile_plan
        from cdf_runtime.codex import model_capabilities
        if args.rollback:
            return perform_profile(root, args.scope, dry=args.dry_run, rollback=True)
        if args.policy is None:
            raise core.CDFError('INVALID_REQUEST', 'An explicit native --policy is required.')
        rendered = native_profile_plan(args.policy, profile=args.profile)
        # Resolve local conflicts before any native capability query.
        perform_profile(root, args.scope, rendered, dry=True)
        capabilities = None
        if args.check or (args.apply and not args.dry_run):
            binary = args.codex or shutil.which('codex')
            if binary is None:
                raise core.CDFError('RUNTIME_UNAVAILABLE', 'Native Codex executable unavailable.')
            runtime_env = None
            if args.scope == 'global' and args.home:
                import os
                runtime_env = dict(os.environ, HOME=str(root), CODEX_HOME=str(root / '.codex'))
            try:
                capabilities = model_capabilities(binary, cwd=root, env=runtime_env)
            except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                raise core.CDFError('RUNTIME_UNAVAILABLE', 'Native capability probe unavailable; no profile was applied.', exit_code=4) from None
        if capabilities is not None:
            rendered = native_profile_plan(args.policy, profile=args.profile, capabilities=capabilities)
        if args.check:
            plan = perform_profile(root, args.scope, rendered, dry=True)
            plan.update(state='available_advertised' if all(role['state'] == 'AVAILABLE_ADVERTISED' for role in rendered['roles'].values()) else 'unavailable',
                        capabilities=capabilities, runtime_routing='NOT_OBSERVED')
            return plan
        return perform_profile(root, args.scope, rendered, dry=not args.apply or args.dry_run)
    if args.action == 'doctor':
        if args.home and args.scope != 'global':
            raise core.CDFError('INVALID_REQUEST', '--home is only valid with global scope.')
        root = core.target_root(args.target, args.scope, args.home)
        executable = args.codex or shutil.which('codex')
        result = {'schema': 1, 'state': 'checked', 'target': str(root),
                  'binary_available': bool(executable), 'version_observed': None}
        if executable:
            try:
                observed = subprocess.run([executable, '--version'], text=True, capture_output=True, timeout=10, check=True)
                result['version_observed'] = observed.stdout.strip() or None
            except (subprocess.SubprocessError, OSError):
                pass
        result['agent_schema_supported'] = 'unverified'
        if args.runtime:
            from cdf_runtime.hooks import runtime_status
            import os
            runtime_env = dict(os.environ, HOME=str(root), CODEX_HOME=str(root / '.codex')) if args.scope == 'global' and args.home else None
            result['runtime'] = runtime_status(args.codex or executable or 'codex', cwd=root, env=runtime_env, plugin_data=args.plugin_data, session_id=args.session_id)
        return result
    if args.action == 'recover':
        if args.home and args.scope != 'global':
            raise core.CDFError('INVALID_REQUEST', '--home is only valid with global scope.')
        root = core.target_root(args.target, args.scope, args.home)
        return core.perform(root, args.scope, 'recover', dry=args.dry_run)
    raise core.CDFError('INVALID_REQUEST', 'Unknown command.')


def main(argv=None):
    args = None
    try:
        args = parser().parse_args(argv)
        result = run(args)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 4 if args.action == 'profile' and args.check and result.get('state') == 'unavailable' else 0
    except core.CDFError as exc:
        if (args is not None and getattr(args, 'dry_run', False)
                and args.action == 'recover'
                and exc.code in {'PATH_COLLISION', 'MANAGED_FILE_MODIFIED',
                                 'MANAGED_BLOCK_MODIFIED', 'MANIFEST_UNSUPPORTED',
                                 'RECOVERY_REQUIRED', 'CONCURRENT_MUTATION'}):
            print(json.dumps({'schema': 1, 'action': 'recover', 'state': 'conflict',
                              'scope': args.scope, 'target': str(Path(args.target).expanduser().absolute()),
                              'planned_actions': [], 'conflicts': exc.paths or [str(exc)],
                              'warnings': [f'{exc.code}: {exc}']}, sort_keys=True))
            return 3 if exc.exit_code == 3 else 2
        print(json.dumps({'schema': 1, 'state': 'error', 'code': exc.code, 'message': str(exc), 'affected_paths': exc.paths, 'next_action': 'Inspect the reported paths and resolve the condition before retrying.'}, sort_keys=True))
        return exc.exit_code
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({'schema': 1, 'state': 'error', 'code': 'IO_FAILURE', 'message': str(exc), 'affected_paths': [], 'next_action': 'Inspect the filesystem and retry when safe.'}, sort_keys=True))
        return 5


if __name__ == '__main__':
    raise SystemExit(main())
