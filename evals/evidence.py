"""Consistency checks for the complete recorded run evidence, not authenticity."""
import hashlib
import json
from pathlib import Path

MANIFEST = 'evidence-manifest.json'
DERIVED = {MANIFEST, 'grading.json', 'graded-run.json', 'grade-manifest.json'}


def _files(folder):
    result = {}
    for path in sorted(folder.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlinks are not accepted in run evidence')
        if path.is_file():
            relative = path.relative_to(folder).as_posix()
            if relative not in DERIVED:
                result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def write_manifest(folder):
    data = {'schema': 1, 'algorithm': 'sha256', 'files': _files(folder)}
    with (folder / MANIFEST).open('x') as out:
        json.dump(data, out, indent=2, sort_keys=True)
        out.write('\n')


def verify_manifest(folder):
    path = folder / MANIFEST
    if path.is_symlink(): raise ValueError('Symlink manifest is not accepted')
    raw = path.read_bytes()
    data = json.loads(raw)
    if (not isinstance(data, dict) or set(data) != {'schema', 'algorithm', 'files'} or
        type(data['schema']) is not int or data['schema'] != 1 or
        data['algorithm'] != 'sha256' or not isinstance(data['files'], dict) or
        data['files'] != _files(folder)):
        raise ValueError('Run evidence manifest mismatch')
    return hashlib.sha256(raw).hexdigest()


def write_grade_manifest(folder):
    files = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
             for name in ('grading.json', 'graded-run.json', MANIFEST)}
    with (folder / 'grade-manifest.json').open('x') as out:
        json.dump({'schema': 1, 'files': files}, out, sort_keys=True, indent=2)
        out.write('\n')


def verify_grade_manifest(folder):
    path = folder / 'grade-manifest.json'
    if path.is_symlink(): raise ValueError('Symlink grade manifest is not accepted')
    data = json.loads(path.read_bytes())
    if not isinstance(data, dict) or type(data.get('schema')) is not int or data.get('schema') != 1 or not isinstance(data.get('files'), dict):
        raise ValueError('Grade manifest mismatch')
    for name in ('grading.json', 'graded-run.json', MANIFEST):
        if (folder / name).is_symlink(): raise ValueError('Symlink grade evidence is not accepted')
    expected = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                for name in ('grading.json', 'graded-run.json', MANIFEST)}
    if data != {'schema': 1, 'files': expected}:
        raise ValueError('Grade manifest mismatch')
