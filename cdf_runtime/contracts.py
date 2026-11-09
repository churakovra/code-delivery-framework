"""Validate the JSON Schema keywords used by CDF's bundled contracts.

This deliberately supports a bounded vocabulary, not arbitrary JSON Schema.
Unknown validation keywords fail closed so changes cannot silently weaken checks.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS = {'$schema', '$id', 'title', 'description', '$comment', 'default', 'examples'}
KEYWORDS = {'type', 'const', 'enum', 'required', 'properties', 'additionalProperties',
            'items', 'uniqueItems', 'minItems', 'maxItems', 'minLength', 'maxLength',
            'pattern', 'minimum', 'maximum'}


class ContractError(ValueError):
    """A value or schema violates a CDF contract."""


def validate(value, schema, path='$'):
    unknown = set(schema) - KEYWORDS - ANNOTATIONS
    if unknown:
        raise ContractError(f'{path}: unsupported schema keywords {sorted(unknown)}')
    types = {'object': lambda v: isinstance(v, dict),
             'array': lambda v: isinstance(v, list),
             'string': lambda v: isinstance(v, str),
             'integer': lambda v: type(v) is int,
             'number': lambda v: type(v) in (int, float),
             'boolean': lambda v: type(v) is bool,
             'null': lambda v: v is None}
    expected = schema.get('type')
    if expected is not None:
        choices = expected if isinstance(expected, list) else [expected]
        if any(t not in types for t in choices):
            raise ContractError(f'{path}: unsupported schema type')
        if not any(types[t](value) for t in choices):
            raise ContractError(f'{path}: expected {expected}')
    if 'const' in schema and (type(value) is not type(schema['const']) or value != schema['const']):
        raise ContractError(f'{path}: unexpected constant')
    if 'enum' in schema and not any(type(value) is type(x) and value == x for x in schema['enum']):
        raise ContractError(f'{path}: value not in enum')
    if isinstance(value, dict):
        missing = set(schema.get('required', [])) - value.keys()
        if missing:
            raise ContractError(f'{path}: missing {sorted(missing)}')
        props = schema.get('properties', {})
        extra = schema.get('additionalProperties', True)
        for key, child in value.items():
            if key in props:
                validate(child, props[key], f'{path}.{key}')
            elif extra is False:
                raise ContractError(f'{path}: unknown field {key}')
            elif isinstance(extra, dict):
                validate(child, extra, f'{path}.{key}')
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', float('inf')):
            raise ContractError(f'{path}: array length outside contract')
        if schema.get('uniqueItems') and len({json.dumps(x, sort_keys=True) for x in value}) != len(value):
            raise ContractError(f'{path}: duplicate items')
        for i, item in enumerate(value):
            if 'items' in schema:
                validate(item, schema['items'], f'{path}[{i}]')
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or len(value) > schema.get('maxLength', float('inf')):
            raise ContractError(f'{path}: string length outside contract')
        if 'pattern' in schema and re.search(schema['pattern'], value) is None:
            raise ContractError(f'{path}: string does not match contract')
    if type(value) in (int, float):
        if isinstance(value, float) and not math.isfinite(value):
            raise ContractError(f'{path}: non-finite number is not valid JSON')
        if value < schema.get('minimum', -float('inf')) or value > schema.get('maximum', float('inf')):
            raise ContractError(f'{path}: number outside contract')


def validate_record(name, value):
    """Validate a named bundled schema, then enforce task-specific invariants."""
    if name not in {'task-state', 'handoff', 'eval-run', 'manifest', 'install-plan', 'transaction-journal'}:
        raise ContractError('Unknown CDF contract')
    validate(value, json.loads((ROOT / 'schemas' / f'{name}.schema.json').read_text()))
    if name == 'task-state':
        if value['state'] in {'READY', 'PLANNING', 'IMPLEMENTING', 'VERIFYING', 'REVIEWING', 'DELIVERED'} and value['open_material_questions']:
            raise ContractError('Dependent work cannot proceed with open material decisions')
        if value['risk'] == 'HIGH' and not value['review_required']:
            raise ContractError('High-risk work requires independent review')
        if value['state'] == 'DELIVERED':
            evidence = value.get('verification', {})
            if evidence.get('status') != 'PASSED':
                raise ContractError('Delivery requires fresh passing verification')
            if value['review_required'] and evidence.get('independent_review') != 'PASSED':
                raise ContractError('Mandatory review must pass before delivery')
    if name == 'handoff' and value['role'] in {'explorer', 'cdf_reviewer', 'cdf_diagnostician'}:
        if value['scope']['write_paths']:
            raise ContractError('Read-only assignment cannot own writes')
    if name == 'eval-run' and value['result'] == 'PASS':
        if not value['acceptance_checks'] or any(c['status'] != 'PASS' for c in value['acceptance_checks']):
            raise ContractError('Unknown, skipped or failing acceptance cannot become PASS')
    if name == 'eval-run':
        checks = value['activation_checks']
        status = value['activation_result']
        if status == 'PASS' and (not checks or any(c['status'] != 'PASS' for c in checks)):
            raise ContractError('Activation PASS requires passing observed checks')
        if status == 'NOT_APPLICABLE' and checks:
            raise ContractError('Activation cannot be not applicable with checks')
        if value['condition'] == 'BASE' and status not in ('NOT_APPLICABLE', 'RUNNER_ERROR'):
            raise ContractError('CDF activation is not applicable to the bare baseline')
        if value['result'] == 'RUNNER_ERROR' and status != 'RUNNER_ERROR':
            raise ContractError('Runner failure cannot have a successful activation result')
    return value
