"""Three-file native profile setup using the existing lock/transaction/recovery.

Unknown agent files are never replaced. The receipt owns only files created by
this setup; unchanged preexisting files remain unowned. No config.toml changes.
"""
import json
from cdf_installer import core
from cdf_registry import PROFILE_AGENTS

RECEIPT = '.codex/cdf/backups/native-agents.json'
PATHS = {role: f'.codex/agents/{role}.toml' for role in PROFILE_AGENTS}


def receipt_read(root, scope):
    raw = core.read_file(root, RECEIPT)
    if raw is None:
        return None, None, None
    try:
        data = json.loads(raw)
        if (set(data) != {'schema', 'scope', 'target', 'profile', 'policy_sha256', 'owned'}
                or type(data['schema']) is not int or data['schema'] != 1 or data['scope'] != scope or data['target'] != str(root)
                or data['profile'] not in ('budget', 'balanced', 'quality')
                or not core.HEX.fullmatch(data['policy_sha256'])
                or not isinstance(data['owned'], dict) or set(data['owned']) - set(PATHS)
                or any(not isinstance(value, str) or not core.HEX.fullmatch(value) for value in data['owned'].values())):
            raise ValueError('Invalid native profile receipt')
        return data, raw, core.mode(root, RECEIPT)
    except (ValueError, TypeError, KeyError):
        raise core.CDFError('MANIFEST_UNSUPPORTED', 'Invalid native profile receipt; preserve it for inspection.', [RECEIPT]) from None


def _op(root, path, after, permissions=0o644, *, validated=None):
    before, previous_mode = validated if validated is not None else (core.read_file(root, path), core.mode(root, path))
    new_mode = permissions if after is not None else None
    return {'path': path, 'operation': ('unchanged' if before == after and previous_mode == new_mode else
                                       'remove' if after is None else 'add' if before is None else 'update'),
            'before_sha256': core.digest(before), 'after_sha256': core.digest(after),
            '_before': before, '_after': after, '_old_mode': previous_mode, '_new_mode': new_mode}


def profile_plan(root, scope, rendered=None, *, rollback=False):
    if core.read_file(root, core.MANIFEST) is not None:
        raise core.CDFError('PATH_COLLISION', 'Remove the legacy CDF installation before separate native profile setup.', [core.MANIFEST])
    if core.safe(root, core.TX).exists() or core.safe(root, core.CLEANUP).exists():
        raise core.CDFError('RECOVERY_REQUIRED', 'Run the existing CDF recovery before profile setup.', [core.TX])
    receipt, receipt_bytes, receipt_mode = receipt_read(root, scope)
    receipt_snapshot = (receipt_bytes, receipt_mode)
    owned = receipt['owned'] if receipt else {}
    ops, new_owned = [], {}
    for role, path in PATHS.items():
        current = core.read_file(root, path)
        current_mode = core.mode(root, path)
        if role in owned and current is not None and core.digest(current) != owned[role]:
            raise core.CDFError('MANAGED_FILE_MODIFIED', 'Native role changed; preserve it and reconcile before retrying.', [path])
        if rollback:
            if role in owned and current is not None:
                ops.append(_op(root, path, None, validated=(current, current_mode)))
            continue
        after = rendered['roles'][role]['content'].encode('utf-8')
        if role not in owned and current is not None and current != after:
            raise core.CDFError('PATH_COLLISION', 'An unowned native agent has this name; it will not be overwritten.', [path])
        ops.append(_op(root, path, after, current_mode or 0o644, validated=(current, current_mode)))
        if role in owned or current is None:
            new_owned[role] = core.digest(after)
    if rollback:
        if receipt:
            ops.append(_op(root, RECEIPT, None, validated=receipt_snapshot))
    else:
        new_receipt = {'schema': 1, 'scope': scope, 'target': str(root),
                       'profile': rendered['profile'], 'policy_sha256': rendered['policy_sha256'], 'owned': new_owned}
        ops.append(_op(root, RECEIPT, (json.dumps(new_receipt, indent=2, sort_keys=True) + '\n').encode(), 0o600, validated=receipt_snapshot))
    ignore = core.private_ignore_plan(root)
    if ignore is not None and not rollback:
        ignore.update(_old_mode=core.mode(root, core.IGNORE), _new_mode=core.mode(root, core.IGNORE) or 0o644)
        ops.insert(0, ignore)
    return ops


def perform_profile(root, scope, rendered=None, *, dry=True, rollback=False):
    ops = profile_plan(root, scope, rendered, rollback=rollback)
    warnings = ['Agent instructions are not a separate sandbox; routing remains unobserved until a real spawn.']
    if scope == 'project':
        warnings.append('Catalog support does not establish project trust or role loading. CDF does not grant trust.')
    if rollback:
        warnings.append('Removes only CDF-created setup; does not restore a previously applied profile. Preexisting roles are preserved.')
    result = core.public_plan(root, scope, 'native-profile-rollback' if rollback else 'native-profile', ops, warnings)
    if dry:
        if rendered is not None:
            result['proposal'] = rendered
        return result
    if not rollback and not all(role['state'] == 'AVAILABLE_ADVERTISED' for role in rendered['roles'].values()):
        raise core.CDFError('RUNTIME_UNAVAILABLE', 'A fresh native model/effort check is required; no fallback was applied.', exit_code=4)
    with core.Lock(root):
        ops = profile_plan(root, scope, rendered, rollback=rollback)
        if any(op['operation'] != 'unchanged' for op in ops):
            if not rollback:
                core.ensure_private_ignore(root)
                # The durable ignore block must precede private receipt/journal creation.
                ops = [op for op in ops if op['path'] != core.IGNORE]
            core.transact(root, scope, 'uninstall' if rollback else 'install', ops, None)
    result.update(state='rolled_back' if rollback else 'configured', native_config_applied=not rollback,
                  runtime_routing='NOT_OBSERVED')
    return result
