"""Small read-only app-server RPC client; no agent or task loop."""
from contextlib import contextmanager
import json
import os
import select
import subprocess
import tempfile
import time


@contextmanager
def app_server(binary, *, cwd, env=None, timeout=20):
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen([str(binary), 'app-server', '--listen', 'stdio://'],
                                   cwd=cwd, env=env, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=errors)
        pending = b''
        serial = 0

        def send(message):
            process.stdin.write((json.dumps(message) + '\n').encode())
            process.stdin.flush()

        def request(method, params):
            nonlocal pending, serial
            serial += 1
            send({'id': serial, 'method': method, 'params': params})
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    message = json.loads(line)
                    if message.get('id') == serial:
                        if 'error' in message:
                            raise ValueError('Native RPC failed: ' + json.dumps(message['error']))
                        return message['result']
                    continue
                if select.select([process.stdout], [], [], max(0, deadline - time.monotonic()))[0]:
                    data = os.read(process.stdout.fileno(), 65536)
                    if not data:
                        raise ValueError('Native app-server exited before responding')
                    pending += data
            raise ValueError('Native app-server request timed out')

        try:
            initialized = request('initialize', {'clientInfo': {'name': 'cdf_runtime_probe', 'version': '1.0.0'},
                                   'capabilities': {'experimentalApi': True}})
            send({'method': 'initialized', 'params': {}})
            yield request, initialized
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            process.stdin.close()
            process.stdout.close()


def model_capabilities(binary, *, cwd, env=None):
    """Advertised pairs only. A catalog does not establish a successful spawn."""
    with app_server(binary, cwd=cwd, env=env) as (request, initialized):
        data, cursor, seen = [], None, set()
        while True:
            page = request('model/list', {'limit': 100, 'includeHidden': False, 'cursor': cursor})
            data.extend(page['data'])
            cursor = page.get('nextCursor')
            if cursor is None:
                break
            if cursor in seen:
                raise ValueError('Native model catalog cursor repeated')
            seen.add(cursor)
        config = request('config/read', {'includeLayers': False})['config']
    pairs = sorted({(entry['model'], effort['reasoningEffort'])
                    for entry in data for effort in entry['supportedReasoningEfforts']})
    return {'source': 'observed_model_list', 'client': initialized.get('userAgent'), 'pairs': pairs,
            'agents_enabled': (config.get('agents') or {}).get('enabled') is not False,
            'spawn_observed': False}
