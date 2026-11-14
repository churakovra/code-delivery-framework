"""Native hook discovery plus explicitly selected local observation history."""
import json
import os
from pathlib import Path
import stat

from cdf_runtime.codex import app_server

EXPECTED = {'sessionStart', 'subagentStart', 'subagentStop'}


def runtime_status(binary, *, cwd, env=None, plugin_data=None, session_id=None):
    result = {'state': 'DEGRADED', 'configured': 'NOT_CHECKED', 'discovered': 'NOT_OBSERVED',
              'observed': 'NOT_OBSERVED', 'enforcement': 'NOT_PROVIDED', 'hooks': [],
              'limitations': ['Historical hook records do not establish current execution or skill application.']}
    try:
        with app_server(binary, cwd=cwd, env=env) as (rpc, initialized):
            entries = rpc('hooks/list', {'cwds': [str(cwd)]})['data']
        result['client'] = initialized.get('userAgent')
        result['configured'] = 'NOT_OBSERVED'
        unhealthy = False
        for entry in entries:
            unhealthy |= bool(entry.get('errors') or entry.get('warnings'))
            for hook in entry['hooks']:
                if (hook.get('pluginId') or '').split('@')[0] != 'code-delivery-framework-desktop':
                    continue
                result['hooks'].append({k: hook.get(k) for k in ('eventName', 'enabled', 'trustStatus', 'source')})
        found = {h['eventName'] for h in result['hooks']}
        if found:
            result['discovered'] = 'DETECTED'
            result['configured'] = 'DETECTED'
        ready = EXPECTED <= found and all(h['enabled'] and h['trustStatus'] in ('trusted', 'managed') for h in result['hooks'])
        result['native_ready'] = ready and not unhealthy
    except (OSError, ValueError, KeyError, TypeError):
        result['limitations'].append('Native hook discovery unavailable; no hook was enabled or trusted by CDF.')
        result['native_ready'] = False
    history_ready = True
    if plugin_data is not None:
        try:
            folder = os.open(Path(plugin_data), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                fd = os.open('events.jsonl', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=folder)
            finally:
                os.close(folder)
            with os.fdopen(fd, 'rb') as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > 1024 * 1024 + 4096:
                    raise ValueError('Invalid log')
                if info.st_size >= 1024 * 1024:
                    history_ready = False
                    result['limitations'].append('Event log is full; observer cannot append until explicitly archived or removed.')
                rows = [json.loads(line) for line in stream.read(1024 * 1024 + 4097).splitlines()]
            rows = [r for r in rows if r.get('schema') == 1 and r.get('source') == 'observed_hook'
                    and (session_id is None or r.get('session_id') == session_id)]
            # Report counts only; never echo arbitrary input or log contents.
            result['recorded_events'] = {name: sum(r.get('event') == name for r in rows)
                                         for name in ('SessionStart', 'SubagentStart', 'SubagentStop')}
            if rows:
                result['observed'] = 'OBSERVED_HISTORY'
        except (OSError, ValueError, TypeError, AttributeError):
            history_ready = False
            result['limitations'].append('Selected event history missing, malformed, unsafe or full.')
    if result['native_ready'] and history_ready:
        result['state'] = 'READY_NOT_EXECUTION_PROOF'
    return result
