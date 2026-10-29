"""Pinned dependency acquisition and staged MCP verification."""
import io
import json
import os
import platform
import queue
import subprocess
import tarfile
import tempfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

def git_package(spec, dest, scratch, *, api):
    """Read exact pinned Git blobs without placing third-party text in the repository."""
    source = spec['path'].strip('/')
    if '..' in Path(source).parts or (source != '.' and (not source.startswith('skills/'))):
        raise api['FrameworkError']('Unsafe upstream skill path')
    git = ['git', '-C', str(scratch)]
    try:
        subprocess.run(['git', 'init', '-q', str(scratch)], check=True, capture_output=True, timeout=30)
        subprocess.run(git + ['fetch', '-q', '--depth=1', spec['repository'], spec['revision']], check=True, capture_output=True, timeout=180)
        got = subprocess.run(git + ['rev-parse', 'FETCH_HEAD'], check=True, capture_output=True, text=True, timeout=10).stdout.strip()
        if got != spec['revision']:
            raise api['FrameworkError']('Pinned source revision mismatch')
        listing = subprocess.run(git + ['ls-tree', '-rz', '--full-tree', got] + ([] if source == '.' else ['--', source]), check=True, capture_output=True, timeout=30).stdout
        files = {}
        for record in listing.split(b'\x00'):
            if not record:
                continue
            meta, raw_path = record.split(b'\t', 1)
            mode, kind, obj = meta.decode().split()
            path = raw_path.decode('utf-8')
            if mode not in ('100644', '100755') or kind != 'blob' or (source != '.' and (not path.startswith(source + '/'))):
                raise api['FrameworkError'](f'Unsafe upstream file: {path}')
            relative = str(Path(dest) / (path if source == '.' else path[len(source) + 1:]))
            if '..' in Path(relative).parts:
                raise api['FrameworkError'](f'Unsafe upstream path: {path}')
            files[relative] = subprocess.run(git + ['cat-file', 'blob', obj], check=True, capture_output=True, timeout=30).stdout
        if f'{dest}/SKILL.md' not in files:
            raise api['FrameworkError'](f'Missing upstream skill: {source}')
        license_listing = subprocess.run(git + ['ls-tree', '-z', got, '--', 'LICENSE'], check=True, capture_output=True, timeout=10).stdout
        if license_listing:
            record = license_listing.rstrip(b'\x00').split(b'\t', 1)
            mode, kind, obj = record[0].decode().split()
            if mode != '100644' or kind != 'blob' or record[1] != b'LICENSE':
                raise api['FrameworkError']('Unsafe upstream license')
            files[f'{dest}/UPSTREAM_LICENSE'] = subprocess.run(git + ['cat-file', 'blob', obj], check=True, capture_output=True, timeout=10).stdout
        return files
    except (OSError, subprocess.SubprocessError) as exc:
        raise api['FrameworkError'](f"Unable to fetch {spec['repository']} at {spec['revision']}: {exc}") from exc

def fetch_dependencies(inventory, *, api):
    """Fetch all required packages before changing the installation target."""
    if not inventory:
        return ({}, {})
    files, versions = ({}, {})
    temporary_base = '/tmp' if os.name != 'nt' and Path('/tmp').is_dir() else None
    with tempfile.TemporaryDirectory(prefix='cdf-', dir=temporary_base) as temporary:
        scratch = Path(temporary)
        for index, (name, spec) in enumerate(inventory['subskills'].items()):
            if spec['kind'] == 'skill':
                package = api['git_package'](spec, f'.agents/skills/{name}', scratch / f'git-{index}')
                files.update(package)
            elif spec['kind'] == 'mcp-integration' and name == 'codebase-memory':
                files.update(api['fetch_codebase_memory'](spec, scratch / 'cbm'))
            else:
                raise api['FrameworkError'](f'Unsupported required dependency: {name}')
            versions[name] = {'revision': spec['revision'], 'kind': spec['kind'], 'license': spec.get('license', 'unverified')}
            if 'release' in spec:
                versions[name]['release'] = spec['release']
    return (files, versions)

def fetch_codebase_memory(spec, scratch, *, api):
    system, machine = (platform.system().lower(), platform.machine().lower())
    if system == 'windows' and machine == 'x86_64':
        machine = 'amd64'
    key = (system, machine)
    if key not in api['CBM_ARCHIVES'] or spec.get('release') != 'v0.12.1':
        raise api['FrameworkError'](f'No verified Codebase Memory release for {system}/{machine}')
    label, expected = api['CBM_ARCHIVES'][key]
    suffix = '.zip' if system == 'windows' else '.tar.gz'
    url = f"https://github.com/DeusData/codebase-memory-mcp/releases/download/{spec['release']}/codebase-memory-mcp-{label}{suffix}"
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            archive = response.read(600000001)
        if len(archive) > 600000000 or api['digest'](archive) != expected:
            raise api['FrameworkError']('Codebase Memory archive checksum mismatch')
        binary_name = 'codebase-memory-mcp.exe' if system == 'windows' else 'codebase-memory-mcp'
        notices = {}
        if system == 'windows':
            with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
                candidates = [x for x in zipped.infolist() if x.filename == binary_name and x.file_size <= 400000000]
                if len(candidates) != 1:
                    raise api['FrameworkError']('Invalid Codebase Memory archive')
                binary = zipped.read(candidates[0])
                for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
                    if name not in zipped.namelist():
                        raise api['FrameworkError'](f'Missing Codebase Memory {name}')
                    notices[f'.codex/delivery-framework/licenses/codebase-memory/{name}'] = zipped.read(name)
        else:
            with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
                candidates = [x for x in tar.getmembers() if x.name in (binary_name, './' + binary_name) and x.isfile() and (x.size <= 400000000)]
                if len(candidates) != 1:
                    raise api['FrameworkError']('Invalid Codebase Memory archive')
                binary = tar.extractfile(candidates[0]).read()
                for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
                    items = [x for x in tar.getmembers() if x.name in (name, './' + name) and x.isfile() and (x.size <= 1000000)]
                    if len(items) != 1:
                        raise api['FrameworkError'](f'Missing Codebase Memory {name}')
                    notices[f'.codex/delivery-framework/licenses/codebase-memory/{name}'] = tar.extractfile(items[0]).read()
        scratch.mkdir(parents=True)
        executable = scratch / binary_name
        executable.write_bytes(binary)
        executable.chmod(493)
        home = scratch / 'home'
        (home / '.codex').mkdir(parents=True)
        runtime_dir = scratch / 'r'
        runtime_dir.mkdir(mode=448)
        env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), CODEX_HOME=str(home / '.codex'), XDG_CACHE_HOME=str(home / '.cache'), CBM_CACHE_DIR=str(home / '.cache/cbm'), CBM_RUNTIME_DIR=str(runtime_dir))
        version = subprocess.run([str(executable), '--version'], env=env, check=True, capture_output=True, text=True, timeout=10).stdout.strip()
        if version != 'codebase-memory-mcp ' + spec['release'].lstrip('v'):
            raise api['FrameworkError'](f'Codebase Memory version mismatch: {version}')
        api['verify_mcp'](executable, env)
        subprocess.run([str(executable), 'install', '--clients=codex', '-y', '--dir=' + str(home / '.local/bin')], env=env, check=True, capture_output=True, timeout=180)
        skill = home / '.codex/skills/codebase-memory'
        result = {f'.codex/delivery-framework/bin/{binary_name}': binary, **notices}
        for item in skill.rglob('*'):
            if item.is_symlink():
                raise api['FrameworkError']('Unsafe Codebase Memory skill symlink')
            if item.is_file():
                result[str(Path('.agents/skills/codebase-memory') / item.relative_to(skill))] = item.read_bytes()
        if '.agents/skills/codebase-memory/SKILL.md' not in result:
            raise api['FrameworkError']('Codebase Memory skill was not provided by its installer')
        return result
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
        raise api['FrameworkError'](f'Unable to prepare Codebase Memory: {exc}') from exc

def verify_mcp(executable, env, *, api):
    """Check a staged MCP server actually initializes and advertises graph tools."""
    messages = queue.Queue()
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen([str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors, env=env)

        def reader():
            try:
                for line in process.stdout:
                    if len(line) > 8000000:
                        break
                    messages.put(line)
            finally:
                messages.put(None)
        thread = threading.Thread(target=reader, daemon=True)
        thread.start()

        def call(number, method, params):
            process.stdin.write((json.dumps({'jsonrpc': '2.0', 'id': number, 'method': method, 'params': params}) + '\n').encode())
            process.stdin.flush()
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                try:
                    line = messages.get(timeout=max(0.01, deadline - time.monotonic()))
                except queue.Empty:
                    break
                if line is None:
                    break
                response = json.loads(line)
                if response.get('id') == number:
                    if 'error' in response:
                        raise api['FrameworkError'](f'MCP rejected {method}')
                    return response['result']
            raise api['FrameworkError'](f'MCP capability check failed: {method}')
        try:
            call(1, 'initialize', {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'delivery-framework', 'version': '1'}})
            process.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
            process.stdin.flush()
            result = call(2, 'tools/list', {})
            names = {tool['name'] for tool in result.get('tools', [])}
            if not {'index_repository', 'search_graph', 'check_index_coverage'}.issubset(names):
                raise api['FrameworkError']('Codebase Memory is missing required graph tools')
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            process.stdin.close()
            process.stdout.close()
