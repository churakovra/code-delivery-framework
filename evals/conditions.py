"""Explicit evaluation guidance identities; snapshots are data, never executable code."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from cdf_installer import core
from cdf_registry import LEGACY_CORE_11, EXTRAS

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_CONDITIONS = ('BASE', 'CDF_20')
CANDIDATE_CONDITIONS = ('BASE', 'LEGACY_CDF_11', 'CANDIDATE_CDF')
ALL_CONDITIONS = HISTORICAL_CONDITIONS + ('LEGACY_CDF_11', 'CANDIDATE_CDF')
HISTORICAL_SHA256 = 'b44f4c3b7cfab44133ff85d3b84bdf2912bd9933122c7b6bd78a5efb4426034b'


def read_snapshot(path, expected_sha256, condition):
    """Validate all bytes before materializing an explicitly selected snapshot.

    A checksum establishes consistency with the supplied identity, not release
    authenticity. The operator must obtain 1.1.0 from a trusted source separately.
    """
    if condition not in ('CDF_20', 'LEGACY_CDF_11'):
        raise ValueError('Not a snapshot condition')
    if path is None or expected_sha256 is None:
        raise ValueError('LEGACY_CDF_11 requires --legacy-snapshot and --legacy-sha256')
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Snapshot must be a regular non-symlink file')
    if not re.fullmatch(r'[a-f0-9]{64}', expected_sha256):
        raise ValueError('Snapshot SHA-256 must be a lowercase hex digest')
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise ValueError('Snapshot SHA-256 mismatch')
    data = json.loads(raw)
    required = {'schema', 'condition', 'framework_version', 'source_revision', 'core', 'files', 'agents_block'}
    if not isinstance(data, dict) or set(data) - required - {'provenance'} or not required <= set(data):
        raise ValueError('Invalid snapshot fields')
    version = '1.1.0' if condition == 'LEGACY_CDF_11' else '1.0.0'
    if (type(data['schema']) is not int or data['schema'] != 1 or data['condition'] != condition or data['framework_version'] != version
            or data['core'] != list(LEGACY_CORE_11)
            or not isinstance(data['source_revision'], str) or not data['source_revision'].strip()):
        raise ValueError('Snapshot version, condition, source or inventory mismatch')
    files = data['files']
    if not isinstance(files, dict) or not all(isinstance(p, str) and isinstance(text, str) for p, text in files.items()):
        raise ValueError('Invalid snapshot payload')
    names = set(LEGACY_CORE_11) | set(sum(EXTRAS.values(), ()))
    fixed = {'.codex/agents/cdf_reviewer.toml', '.codex/agents/cdf_diagnostician.toml', '.codex/cdf/subskills.catalog.json'}
    seen = set()
    for name in files:
        try:
            p = core.relative_path(name)
        except core.CDFError as exc:
            raise ValueError('Unsafe snapshot path') from exc
        if (name not in fixed and not (len(p.parts) >= 4 and p.parts[:2] == ('.agents', 'skills') and p.parts[2] in names)):
            raise ValueError('Unknown snapshot payload path')
        # Case collisions are rejected even on case-sensitive test filesystems.
        for length in range(1, len(p.parts) + 1):
            prefix = PurePosixPath(*p.parts[:length]).as_posix()
            key = prefix.casefold()
            if any(old.casefold() == key and old != prefix for old in seen):
                raise ValueError('Case-colliding snapshot paths')
            seen.add(prefix)
    required_paths = fixed | {f'.agents/skills/{name}/SKILL.md' for name in LEGACY_CORE_11}
    if not required_paths <= set(files):
        raise ValueError('Snapshot lacks required guidance files')
    block = data['agents_block']
    if (not isinstance(block, str) or block.count(core.START.decode()) != 1
            or block.count(core.END.decode()) != 1 or not block.startswith(core.START.decode())
            or not block.rstrip('\r\n').endswith(core.END.decode())):
        raise ValueError('Invalid snapshot managed policy')
    return data, actual


def selected_snapshot(condition, legacy_snapshot=None, legacy_sha256=None):
    if condition == 'CDF_20':
        return read_snapshot(ROOT / 'evals/baselines/cdf-20.json', HISTORICAL_SHA256, condition)
    return read_snapshot(legacy_snapshot, legacy_sha256, condition)


def install_snapshot(workspace, snapshot):
    """Materialize validated guidance in a disposable fixture, preserving user text."""
    def target(name):
        try:
            return core.safe(workspace, name)
        except core.CDFError as exc:
            raise ValueError('Unsafe or colliding snapshot destination') from exc

    # Check every destination before writing any guidance. This is a disposable
    # eval setup, not a substitute for the production journaled installer.
    for name in snapshot['files']:
        if target(name).exists():
            raise ValueError('Snapshot guidance collides with fixture content')
    agents = target('AGENTS.md')
    original = agents.read_bytes() if agents.exists() else b''
    if core.START in original or core.END in original:
        raise ValueError('Fixture already contains a managed policy')
    for name, text in snapshot['files'].items():
        path = target(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        target(name).write_text(text, encoding='utf-8')
    block = snapshot['agents_block'].encode()
    target('AGENTS.md').write_bytes(original + (b'\n' if original and not original.endswith(b'\n') else b'') + block)


def validate_guidance_identity(folder, condition, environment):
    """Validate new snapshot evidence while allowing archived historical records."""
    identity = environment.get('snapshot_identity')
    if condition == 'CDF_20' and identity is None:
        return  # Archived runs predate frozen guidance evidence.
    if condition not in ('CDF_20', 'LEGACY_CDF_11'):
        return
    if not isinstance(identity, dict):
        raise ValueError('Missing frozen guidance identity')
    expected = HISTORICAL_SHA256 if condition == 'CDF_20' else identity.get('sha256')
    snapshot, actual = read_snapshot(folder / 'guidance-snapshot.json', expected, condition)
    if (identity.get('sha256') != actual or identity.get('source_revision') != snapshot['source_revision']
            or identity.get('framework_version') != snapshot['framework_version']):
        raise ValueError('Frozen guidance evidence differs from environment identity')
