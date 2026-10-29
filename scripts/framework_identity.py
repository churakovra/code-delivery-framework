"""Framework version and source identity."""
import re
import subprocess
from pathlib import Path
import tomllib

class FrameworkError(Exception):
    pass

def framework_version(root):
    path = root/'pyproject.toml'
    if not path.is_file():
        raise FrameworkError('Framework version metadata is missing')
    version = tomllib.loads(path.read_text()).get('project', {}).get('version')
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+(?:\.dev\d+)?', version):
        raise FrameworkError('Invalid framework version')
    return version

def version_key(version):
    match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)(?:\.dev(\d+))?', version)
    if not match:
        raise FrameworkError('Invalid installed framework version')
    major, minor, patch, development = match.groups()
    return (int(major), int(minor), int(patch), 1 if development is None else 0, int(development or 0))

def source_identity(root):
    """Report checkout identity or the revision embedded by git archive."""
    unknown = {'revision': None, 'dirty': None}
    def archive_identity():
        path = root/'SOURCE_REVISION'
        if not path.is_file(): return unknown
        revision = path.read_text().strip()
        return {'revision': revision, 'dirty': None, 'origin': 'archive'} if re.fullmatch(r'[0-9a-f]{40,64}', revision) else unknown
    try:
        top = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], check=True, capture_output=True, text=True, timeout=5).stdout.strip()
        if Path(top).resolve() != root.resolve():
            return archive_identity()
        revision = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True, timeout=5).stdout.strip()
        dirty = subprocess.run(['git', '-C', str(root), 'status', '--porcelain', '--untracked-files=normal'], check=True, capture_output=True, text=True, timeout=5).stdout != ''
        if not re.fullmatch(r'[0-9a-f]{40,64}', revision):
            return unknown
        return {'revision': revision, 'dirty': dirty}
    except (OSError, subprocess.SubprocessError):
        return archive_identity()

def check_upgrade_version(previous, target_version):
    installed = previous.get('framework_version') if previous else None
    if installed is not None:
        if not isinstance(installed, str):
            raise FrameworkError('Invalid installed framework version')
        if target_version and version_key(installed) > version_key(target_version):
            raise FrameworkError(f'Downgrade from {installed} to {target_version} is not supported')

