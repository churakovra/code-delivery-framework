#!/usr/bin/env python3
"""Offline CDF2 skill/catalog/agent/contract checks; no model or network calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cdf_runtime.contracts import validate_record
from cdf_registry import CORE, EXTRAS, NATIVE_AGENTS, inventory_markdown


def validate_source(root=ROOT):
    skills = {p.parent.name: p for p in (root / 'skills').glob('cdf-*/SKILL.md')}
    expected = set(CORE).union(*EXTRAS.values())
    if len(CORE) + sum(map(len, EXTRAS.values())) != len(expected):
        raise ValueError('Bundle inventory contains duplicate skills')
    if (root / 'docs/bundle-inventory.md').read_text() != inventory_markdown():
        raise ValueError('Stale bundle inventory documentation; run --write-inventory')
    if skills.keys() != expected:
        raise ValueError('Skill folders differ from the bundle inventory')
    catalog = json.loads((root / 'subskills.catalog.json').read_text())
    candidates = catalog['candidates']
    for name, p in skills.items():
        text = p.read_text()
        if not text.startswith('---\n') or '\n---\n' not in text[4:]:
            raise ValueError(f'{name}: missing frontmatter')
        header = text.split('---', 2)[1]
        if not re.search(r'^name:\s*' + re.escape(name) + r'\s*$', header, re.M):
            raise ValueError(f'{name}: name differs from folder')
        desc = re.search(r'^description:\s*(.+)$', header, re.M)
        if not desc or not 1 <= len(desc[1]) <= 1024:
            raise ValueError(f'{name}: invalid description')
        if 'Fallback:' not in text:
            raise ValueError(f'{name}: no local fallback')
        for relative in re.findall(r'`(references/[^`]+\.md)`', text):
            if '..' in Path(relative).parts or not (p.parent / relative).is_file():
                raise ValueError(f'{name}: unresolved local reference {relative}')
        routes = text.split('## Optional subskills', 1)[1]
        for key in re.findall(r'^- `([^`]+)`:', routes, re.M):
            if key not in candidates or name not in candidates[key]['cdf_skills']:
                raise ValueError(f'{name}: unknown or unowned candidate {key}')
    for key, item in candidates.items():
        if not item.get('activation') or not item.get('license_note') or not item.get('source_url', '').startswith('https://'):
            raise ValueError(f'{key}: incomplete provenance or activation')
        if item['revision'] is not None and not re.fullmatch('[a-f0-9]{40}', item['revision']):
            raise ValueError(f'{key}: invalid pinned revision')
        if not item['cdf_skills'] or not set(item['cdf_skills']) <= expected:
            raise ValueError(f'{key}: invalid primary owner')
    for name in NATIVE_AGENTS:
        fields = tomllib.loads((root / 'templates' / f'{name}.toml').read_text())
        if fields.get('name') != name or not all(fields.get(k) for k in ('description', 'developer_instructions')):
            raise ValueError(f'{name}: invalid native agent')
        if {'model', 'model_reasoning_effort'} & fields.keys():
            raise ValueError(f'{name}: unexpected pinned model')
    operator = (root / 'skills/cdf-model-calibration/agents/openai.yaml').read_text()
    if not re.search(r'^  allow_implicit_invocation: false$', operator, re.M):
        raise ValueError('Operator skill must be explicit-only')
    examples = root / 'docs/plans/cdf-2.0/templates'
    for example, schema in [('handoff', 'handoff'), ('install-plan', 'install-plan'), ('task-checkpoint', 'task-state')]:
        validate_record(schema, json.loads((examples / f'{example}.example.json').read_text()))
    return {'state': 'passed', 'core_skills': len(CORE), 'optional_skills': sum(map(len, EXTRAS.values())),
            'community_candidates': len(candidates), 'native_agent_templates': len(NATIVE_AGENTS),
            'runtime_behavior': 'not_evaluated', 'network': 'not_used'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-inventory', action='store_true', help='Regenerate bundle inventory documentation')
    args = parser.parse_args()
    if args.write_inventory:
        (ROOT / 'docs/bundle-inventory.md').write_text(inventory_markdown())
    try:
        result = validate_source()
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({'state': 'error', 'message': str(exc)}))
        raise SystemExit(2)
    print(json.dumps(result, indent=2))
