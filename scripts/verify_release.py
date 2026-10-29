#!/usr/bin/env python3
"""Verify a release archive against an independently obtained SHA-256 and identity."""
import argparse
import hashlib
import re
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import PurePosixPath


def verify(path, expected_sha256, expected_version, expected_revision):
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha256) or not re.fullmatch(r'[0-9a-f]{40,64}', expected_revision):
        raise ValueError('Expected SHA-256 or revision is invalid')
    with open(path, 'rb') as source, tempfile.TemporaryFile() as stream:
        h = hashlib.sha256()
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            h.update(chunk)
            stream.write(chunk)
        if h.hexdigest() != expected_sha256:
            raise ValueError('Archive checksum mismatch')
        stream.seek(0)
        if zipfile.is_zipfile(stream):
            with zipfile.ZipFile(stream) as archive:
                entries = []
                for item in archive.infolist():
                    if not item.is_dir() and len(PurePosixPath(item.filename).parts) in (1, 2) and PurePosixPath(item.filename).name in ('pyproject.toml', 'SOURCE_REVISION'):
                        if item.file_size > 1_000_000: raise ValueError('Release identity file is too large')
                        entries.append((item.filename, archive.read(item)))
        else:
            stream.seek(0)
            with tarfile.open(fileobj=stream, mode='r:*') as archive:
                entries = []
                for item in archive.getmembers():
                    if item.isfile() and len(PurePosixPath(item.name).parts) in (1, 2) and PurePosixPath(item.name).name in ('pyproject.toml', 'SOURCE_REVISION'):
                        if item.size > 1_000_000: raise ValueError('Release identity file is too large')
                        entries.append((item.name, archive.extractfile(item).read()))
    candidates = {}
    for name, content in entries:
        parts = PurePosixPath(name).parts
        if len(parts) not in (1, 2) or parts[-1] not in ('pyproject.toml', 'SOURCE_REVISION'):
            continue
        if parts[-1] in candidates:
            raise ValueError('Duplicate release identity file')
        candidates[parts[-1]] = (parts[:-1], content)
    if set(candidates) != {'pyproject.toml', 'SOURCE_REVISION'} or candidates['pyproject.toml'][0] != candidates['SOURCE_REVISION'][0]:
        raise ValueError('Release identity files are missing or ambiguous')
    version = tomllib.loads(candidates['pyproject.toml'][1].decode())['project']['version']
    revision = candidates['SOURCE_REVISION'][1].decode().strip()
    if version != expected_version or revision != expected_revision:
        raise ValueError('Release version or revision mismatch')
    return {'sha256': expected_sha256, 'version': version, 'revision': revision}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive')
    parser.add_argument('--sha256', required=True, help='SHA-256 from an independent trusted channel')
    parser.add_argument('--version', required=True)
    parser.add_argument('--revision', required=True, help='Trusted full Git revision')
    args = parser.parse_args()
    try:
        result = verify(args.archive, args.sha256, args.version, args.revision)
    except (ValueError, OSError, KeyError, tarfile.TarError, zipfile.BadZipFile) as exc:
        parser.exit(1, f'Blocked: {exc}\n')
    print(f'Verified {result["version"]} at {result["revision"]}; SHA-256 {result["sha256"]}')


if __name__ == '__main__':
    main()
