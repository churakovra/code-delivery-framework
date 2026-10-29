"""Command-line interface for the delivery framework."""
import argparse
import json
import sys
import tomllib
from pathlib import Path

def main(argv=None, api=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['install', 'upgrade', 'recover', 'status', 'uninstall', 'validate', 'select-models', 'apply-models', 'sync-models'])
    parser.add_argument('--target', type=Path, default=Path.cwd())
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--global', dest='global_mode', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--deep-preview', action='store_true', help='Download and verify dependencies during an install or upgrade dry run')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--codex', default='codex')
    parser.add_argument('--selection-profile', type=Path, help='User-provided TOML selection context')
    parser.add_argument('--model-policy', type=Path, help='Explicit TOML role policy for installation (no research)')
    parser.add_argument('--proposal', type=Path, help='Reviewed JSON model proposal to apply')
    args = parser.parse_args(argv)
    try:
        target = args.target.absolute()
        home = args.home.absolute()
        if target.is_symlink() or target.resolve() != target:
            raise api['FrameworkError']('Target must be a canonical path without symlinks')
        if args.global_mode and target != home:
            raise api['FrameworkError']('--global requires --target equal to --home')
        if not args.global_mode and target == home:
            raise api['FrameworkError']('Installing at home requires explicit --global')
        if args.model_policy and args.command != 'install':
            raise api['FrameworkError']('--model-policy applies only to install')
        if args.selection_profile and args.command != 'select-models':
            raise api['FrameworkError']('--selection-profile applies only to select-models')
        if args.offline and args.command != 'validate':
            raise api['FrameworkError']('--offline is allowed only for static validate')
        if args.dry_run and args.command not in ('install', 'upgrade', 'uninstall'):
            raise api['FrameworkError']('--dry-run applies only to install/upgrade/uninstall')
        if args.deep_preview and (not args.dry_run or args.command not in ('install', 'upgrade')):
            raise api['FrameworkError']('--deep-preview requires install or upgrade with --dry-run')
        if args.command in ('install', 'upgrade', 'validate', 'select-models', 'apply-models', 'sync-models'):
            _, _, policy, roles = api['payload']()
            if args.model_policy:
                policy = tomllib.loads(args.model_policy.read_text())
                if set(policy) != {role['policy'] for role in roles.values()}:
                    raise api['FrameworkError']('Supplied policy must contain exactly the active role policy sections')
                api['payload'](selected_policy=policy)
            if not args.offline and (not args.dry_run):
                version, models = api['probe'](args.codex)
                if args.command == 'validate':
                    installed = api['safe'](target, '.codex/delivery-framework/model-policy.toml')
                    api['compatibility'](tomllib.loads(installed.read_text()) if installed.is_file() else policy, roles, models)
            if args.command in ('select-models', 'apply-models', 'sync-models'):
                installed_manifest = api['read_manifest'](target)
                scope = 'global' if args.global_mode else 'project'
                if not installed_manifest or installed_manifest.get('scope') != scope:
                    raise api['FrameworkError']('Installation scope does not match target')
            if args.command == 'sync-models':
                result = api['sync_models'](target, roles, models)
            elif args.command == 'select-models':
                if args.dry_run:
                    raise api['FrameworkError']('select-models does not use --dry-run')
                installed = api['safe'](target, '.codex/delivery-framework/model-policy.toml')
                if not api['read_manifest'](target) or not installed.is_file():
                    raise api['FrameworkError']('No installed model policy')
                health = api['status'](target)
                if health.get('state') != 'installed' or any((value != 'clean' for value in health.get('files', {}).values())) or any((value != 'clean' for value in health.get('reused', {}).values())) or (health.get('external_mcp', 'clean') != 'clean'):
                    raise api['FrameworkError']('Installation is not clean; resolve status before selecting models')
                manifest_hash = api['digest'](api['safe'](target, api['STATE']).read_bytes())
                current = tomllib.loads(installed.read_text())
                context = api['read_selection_profile'](args.selection_profile)
                selection = api['select_policy'](args.codex, models, roles, context, current=current)
                result = api['model_proposal'](current, selection['policy'], api['selection_report'](selection, context), target, manifest_hash)
            elif args.command == 'apply-models':
                if not args.proposal:
                    raise api['FrameworkError']('apply-models requires --proposal')
                proposal = json.loads(args.proposal.read_text())
                result = api['apply_model_proposal'](target, roles, models, proposal)
            elif args.command == 'validate':
                result = {'static': 'passed', 'runtime': 'unchecked (offline)' if args.offline else version, 'models': 'unchecked (offline)' if args.offline else 'available'}
            elif args.command == 'upgrade':
                installed = api['safe'](target, '.codex/delivery-framework/model-policy.toml')
                selected = tomllib.loads(installed.read_text()) if installed.is_file() else policy
                if not args.offline and (not args.dry_run):
                    api['compatibility'](selected, roles, models)
                result = api['install_with_dependencies'](target, args.dry_run, global_mode=args.global_mode, upgrade=True, selected_policy=selected, deep_preview=args.deep_preview)
                if not args.dry_run:
                    result['welcome'] = api['welcome'](roles, selected)
                    result['availability'] = api['installation_availability'](args.codex, target, args.home, args.global_mode)
            else:
                if args.dry_run:
                    if args.deep_preview:
                        report = api['provisional_report'](policy, args.model_policy)
                        result = api['install_with_dependencies'](target, True, global_mode=args.global_mode, selected_policy=policy, report=report, deep_preview=True)
                    else:
                        result = api['install'](target, True, global_mode=args.global_mode, selected_policy=policy)
                    result['model_selection'] = 'not run in dry run'
                else:
                    if api['read_manifest'](target) or api['safe'](target, '.codex/delivery-framework/transaction').exists():
                        raise api['FrameworkError']('Existing installation or recovery transaction: inspect status before installing')
                    selected = policy
                    api['compatibility'](selected, roles, models)
                    report = api['provisional_report'](selected, args.model_policy)
                    result = api['install'](target, False, global_mode=args.global_mode, selected_policy=selected, report=report)
                    result['model_selection'] = report
                    result['welcome'] = api['welcome'](roles, selected)
                if not args.dry_run:
                    result['availability'] = api['installation_availability'](args.codex, target, args.home, args.global_mode)
        elif args.command == 'status':
            result = api['status'](target)
        elif args.command == 'recover':
            result = api['recover'](target)
        else:
            result = api['uninstall'](target, args.dry_run)
        if args.dry_run and args.command in ('install', 'upgrade'):
            result['runtime_check'] = 'not run in dry run'
        print(json.dumps(result, indent=2))
        return 1 if result.get('state') == 'blocked' else 0
    except (api['FrameworkError'], OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'state': 'blocked', 'error': str(exc)}))
        print(f'Blocked: {exc}', file=sys.stderr)
        return 1
