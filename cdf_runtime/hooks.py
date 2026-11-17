"""Read-only native plugin/skill/hook discovery and selected emission history."""
import json
import os
from pathlib import Path
import re
import stat
import subprocess

from cdf_registry import CORE
from cdf_runtime.codex import app_server

EXPECTED = {'sessionStart', 'userPromptSubmit', 'subagentStart'}
PLUGIN = 'code-delivery-framework'
EVENTS = ('SessionStart', 'UserPromptSubmit', 'SubagentStart')


def runtime_status(binary, *, cwd, env=None, plugin_data=None, session_id=None):
    result = {'state': 'DEGRADED', 'configured': 'NOT_CHECKED', 'discovered': 'NOT_OBSERVED',
              'observed': 'NOT_OBSERVED', 'context_emitted': 'NOT_OBSERVED',
              'context_receipt': 'NOT_OBSERVED', 'method_application': 'NOT_OBSERVED',
              'enforcement': 'NOT_PROVIDED', 'hooks': [], 'hook_trust': 'UNKNOWN',
              'plugin': {'installed': 'UNKNOWN', 'enabled': 'UNKNOWN'},
              'skills': {'discovered': 'NOT_OBSERVED', 'expected': len(CORE), 'enabled_count': 0},
              'limitations': ['Context emitted on stdout is not proof of model receipt or method application.',
                              'Selected hook history is historical, not current execution evidence.']}
    unhealthy = False
    try:
        with app_server(binary, cwd=cwd, env=env) as (rpc, initialized):
            result['client'] = initialized.get('userAgent')
            try:
                catalog = rpc('plugin/list', {'cwds': [str(cwd)]})
                plugins = [p for market in catalog['marketplaces'] for p in market.get('plugins', [])]
                primary = [p for p in plugins if (p.get('id') or '').split('@')[0] == PLUGIN]
                installed = [p for p in primary if p.get('installed') is True]
                result['plugin'] = {'installed': 'DETECTED' if installed else 'NOT_DETECTED',
                                    'enabled': any(p.get('enabled') is True for p in installed)}
                if catalog.get('marketplaceLoadErrors'):
                    unhealthy = True
                    result['limitations'].append('Native marketplace discovery reported errors.')
                if any((p.get('id') or '').split('@')[0] == PLUGIN + '-desktop' and p.get('enabled') for p in plugins):
                    unhealthy = True
                    result['limitations'].append('Legacy desktop plugin is enabled; remove it explicitly to avoid overlapping hooks/skills.')
            except (ValueError, KeyError, TypeError):
                result['limitations'].append('Native plugin installation state unavailable.')
            try:
                rows = rpc('skills/list', {'cwds': [str(cwd)], 'forceReload': True})['data']
                expected = {PLUGIN + ':' + name for name in CORE}
                found = {s['name'] for row in rows for s in row['skills']
                         if s.get('enabled') is True and s.get('name') in expected}
                errors = any(row.get('errors') for row in rows)
                result['skills'] = {'discovered': 'DETECTED' if expected <= found and not errors else 'INCOMPLETE',
                                    'expected': len(CORE), 'enabled_count': len(found),
                                    'missing': sorted(expected - found)}
                unhealthy |= errors
            except (ValueError, KeyError, TypeError):
                result['limitations'].append('Native skill discovery unavailable.')
            entries = rpc('hooks/list', {'cwds': [str(cwd)]})['data']
        result['configured'] = 'NOT_OBSERVED'
        for entry in entries:
            entry_hooks = entry.get('hooks', [])
            owns_cdf_hook = any((hook.get('pluginId') or '').split('@')[0] == PLUGIN for hook in entry_hooks)
            if owns_cdf_hook:
                unhealthy |= bool(entry.get('errors') or entry.get('warnings'))
            for hook in entry_hooks:
                if (hook.get('pluginId') or '').split('@')[0] == PLUGIN:
                    result['hooks'].append({key: hook.get(key) for key in ('eventName', 'enabled', 'trustStatus', 'source')})
        unexpected = {h['eventName'] for h in result['hooks']} - EXPECTED
        if unexpected:
            unhealthy = True
            result['limitations'].append('Unexpected CDF hook events detected; reinstall the current package.')
        counts = {event: sum(h['eventName'] == event for h in result['hooks']) for event in EXPECTED}
        result['hook_counts'] = counts
        duplicates = any(count > 1 for count in counts.values())
        if result['hooks']:
            result['discovered'] = result['configured'] = 'DETECTED'
            result['hook_trust'] = ('TRUSTED' if all(h['trustStatus'] in ('trusted', 'managed') for h in result['hooks'])
                                    else 'UNTRUSTED' if any(h['trustStatus'] == 'untrusted' for h in result['hooks']) else 'UNKNOWN')
        if duplicates:
            result['limitations'].append('Duplicate CDF hook registrations detected.')
        ready = all(count == 1 for count in counts.values()) and not duplicates
        result['native_ready'] = (ready and result['hook_trust'] == 'TRUSTED'
                                  and all(h['enabled'] is True for h in result['hooks']) and not unhealthy
                                  and result['plugin']['installed'] == 'DETECTED' and result['plugin']['enabled'] is True
                                  and result['skills']['discovered'] == 'DETECTED')
        if not result['hooks']:
            result['limitations'].append('No CDF hooks discovered. This client may require the compatibility layout; rebuild for its --codex path.')
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        result['limitations'].append('Native hook discovery unavailable; CDF did not change hook trust or permissions.')
        result['native_ready'] = False
    history_ready = True
    if plugin_data is not None:
        try:
            directory = os.open(Path(plugin_data), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                fd = os.open('events.jsonl', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            finally:
                os.close(directory)
            with os.fdopen(fd, 'rb') as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > 1024 * 1024 + 4096:
                    raise ValueError('Invalid log')
                if info.st_size >= 1024 * 1024:
                    history_ready = False
                    result['limitations'].append('Event log full; archive or remove it explicitly to resume recording.')
                rows = [json.loads(line) for line in stream.read(1024 * 1024 + 4097).splitlines()]
            rows = [r for r in rows if isinstance(r, dict) and r.get('schema') == 1 and r.get('source') == 'observed_hook'
                    and r.get('event') in EVENTS and (session_id is None or r.get('session_id') == session_id)]
            result['recorded_events'] = {name: sum(r.get('event') == name for r in rows) for name in EVENTS}
            emitted = [r for r in rows if r.get('context_emitted') is True and isinstance(r.get('context_sha256'), str)
                       and re.fullmatch('[a-f0-9]{64}', r['context_sha256'])]
            result['emitted_context_events'] = {name: sum(r.get('event') == name for r in emitted) for name in EVENTS}
            if rows:
                result['observed'] = 'OBSERVED_HISTORY'
            if emitted:
                result['context_emitted'] = 'OBSERVED_HISTORY'
        except (OSError, ValueError, TypeError):
            history_ready = False
            result['limitations'].append('Selected event history missing, malformed, unsafe or full.')
    if result['native_ready'] and history_ready:
        result['state'] = 'READY_NOT_EXECUTION_PROOF'
    return result
