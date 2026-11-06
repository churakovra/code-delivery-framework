#!/usr/bin/env python3
"""Static consistency checks for this planning artifact; no Codex model calls."""
from __future__ import annotations
import json
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
ISSUES: list[str] = []

for path in sorted(ROOT.rglob('*.json')):
    try:
        json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        ISSUES.append(f'Invalid JSON {path.relative_to(ROOT)}: {exc}')
for path in sorted(ROOT.rglob('*.toml')):
    try:
        tomllib.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        ISSUES.append(f'Invalid TOML {path.relative_to(ROOT)}: {exc}')

for name in ('cdf_reviewer', 'cdf_diagnostician'):
    path = ROOT / 'templates' / f'{name}.toml'
    value = tomllib.loads(path.read_text())
    if value.get('name') != name:
        ISSUES.append(f'Wrong name in {path}')
    if not all(value.get(f) for f in ('name', 'description', 'developer_instructions')):
        ISSUES.append(f'Missing custom agent required fields: {path}')
    for setting in ('model', 'model_reasoning_effort'):
        if setting in value:
            ISSUES.append(f'Unexpected pinned {setting} in {path}')

core = ['cdf-backend', 'cdf-code-review', 'cdf-codebase-research', 'cdf-debugging', 'cdf-documentation', 'cdf-frontend', 'cdf-implementation', 'cdf-orchestration', 'cdf-planning', 'cdf-requirements', 'cdf-ui-design', 'cdf-verification']
extras = ['cdf-model-calibration', 'cdf-explain', 'cdf-teach']
if len(set(core + extras)) != 15 or len(core) != 12:
    ISSUES.append('Unexpected skill catalog count')

meta = json.loads((ROOT/'evals/golden-cases.json').read_text())
if len({c['id'] for c in meta['cases']}) != len(meta['cases']):
    ISSUES.append('Duplicate eval case IDs')
if len(meta['cases']) < 14:
    ISSUES.append('Insufficient eval coverage')

for p in (ROOT/'docs').glob('*.md'):
    txt = p.read_text()
    for name in re.findall(r'\]\((\.\./[^)#]+\.md)\)', txt):
        if not (p.parent/name).resolve().exists():
            ISSUES.append(f'Broken relative markdown link: {p}: {name}')

print(f'Planning files: {sum(1 for x in ROOT.rglob("*") if x.is_file())}.')
print(f'Core/extras: {len(core)} / {len(extras)}; eval cases: {len(meta["cases"])}.')
if ISSUES:
    print('FAILED:')
    for issue in ISSUES:
        print(' -', issue)
    raise SystemExit(1)
print('Static blueprint validation PASSED (does not imply agent/installer runtime acceptance).')
