"""Offline CDF2 contracts; these checks do not score agent compliance."""
import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import tomllib
import unittest

from cdf_runtime.contracts import ContractError, validate, validate_record
from cdf_runtime.policy import resolve_child, load_policy, delegation_decision

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_kernel_without_external_routes_still_validates_and_checks_references(self):
        from scripts.validate_cdf import validate_source
        from cdf_installer.core import parse_skill, CDFError
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            for name in ('skills', 'docs', 'templates'):
                shutil.copytree(ROOT / name, target / name)
            shutil.copyfile(ROOT / 'subskills.catalog.json', target / 'subskills.catalog.json')
            kernel = target / 'skills/cdf/SKILL.md'
            text = kernel.read_text().split('## Optional subskills', 1)[0] + 'Fallback: local delivery methods.\n'
            kernel.write_text(text)
            self.assertEqual(validate_source(target)['core_skills'], 10)
            parse_skill(kernel, 'cdf')
            reference = target / 'skills/cdf/references/quality-contract.md'
            reference.unlink()
            with self.assertRaisesRegex(ValueError, 'unresolved local reference'):
                validate_source(target)
            with self.assertRaises(CDFError) as caught:
                parse_skill(kernel, 'cdf')
            self.assertEqual(caught.exception.code, 'INVALID_BUNDLE')

    def test_source_contains_only_registered_skills(self):
        from scripts.validate_cdf import validate_source
        self.assertEqual(validate_source()['core_skills'], 10)
        from cdf_registry import CORE, EXTRAS
        expected = set(CORE).union(*EXTRAS.values())
        self.assertEqual({p.name for p in (ROOT / 'skills').iterdir()}, expected)

    def test_examples_and_required_review(self):
        source = ROOT / 'templates/examples'
        for example, schema in [('task-checkpoint', 'task-state'), ('handoff', 'handoff'), ('install-plan', 'install-plan')]:
            record = json.loads((source / f'{example}.example.json').read_text())
            validate_record(schema, record)
        task = json.loads((source / 'task-checkpoint.example.json').read_text())
        task['state'] = 'IMPLEMENTING'
        task['open_material_questions'] = ['Who may delete this resource?']
        with self.assertRaises(ContractError):
            validate_record('task-state', task)
        task['open_material_questions'] = []
        task['review_required'] = False
        with self.assertRaises(ContractError):
            validate_record('task-state', task)

    def test_delivery_cannot_hide_missing_review(self):
        task = json.loads((ROOT / 'templates/examples/task-checkpoint.example.json').read_text())
        task['state'] = 'DELIVERED'
        task['verification'] = {'status': 'PASSED'}
        with self.assertRaises(ContractError):
            validate_record('task-state', task)
        task['verification']['independent_review'] = 'PASSED'
        validate_record('task-state', task)

    def test_read_only_handoff_rejects_write_ownership(self):
        handoff = json.loads((ROOT / 'templates/examples/handoff.example.json').read_text())
        handoff['scope']['write_paths'] = ['app.py']
        with self.assertRaises(ContractError):
            validate_record('handoff', handoff)

    def test_schema_nested_types_unknown_keywords_and_bounds(self):
        schema = {'type': 'object', 'additionalProperties': False, 'required': ['n'],
                  'properties': {'n': {'type': 'integer', 'minimum': 0}}}
        validate({'n': 0}, schema)
        for value in [{'n': True}, {'n': -1}, {'n': 0, 'extra': 1}, {}]:
            with self.subTest(value=value), self.assertRaises(ContractError):
                validate(value, schema)
        with self.assertRaises(ContractError):
            validate({}, {'type': 'object', 'oneOf': []})
        with self.assertRaises(ContractError):
            validate(['x', 'x'], {'type': 'array', 'uniqueItems': True})

    def test_unknown_acceptance_is_not_a_pass(self):
        record = {'schema': 1, 'case_id': 'G09', 'condition': 'CDF_20', 'seed': 0,
                  'runtime_version': 'test', 'model_requested': None, 'model_observed': None,
                  'result': 'PASS', 'acceptance_checks': [{'name': 'independent review', 'status': 'NOT_OBSERVED'}],
                  'resource_measurement': {'basis': 'not_available'}, 'raw_trace_path': 'trace.ndjson'}
        with self.assertRaises(ContractError):
            validate_record('eval-run', record)


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = tomllib.loads((ROOT / 'policies/model-routing.example.toml').read_text())

    def test_request_is_not_confirmation(self):
        pair = ('gpt-6.1-terra', 'low')
        result = resolve_child(self.policy, role='worker', tier='t1', catalog={pair}, override_supported=True)
        self.assertEqual(result.state, 'requested_unconfirmed')
        self.assertIsNone(result.observed_model)
        result = resolve_child(self.policy, role='worker', tier='t1', catalog={pair}, override_supported=True, observed=pair)
        self.assertEqual(result.state, 'confirmed')

    def test_malformed_candidate_tables_return_clean_cli_errors(self):
        source = (ROOT / 'policies/model-routing.example.toml').read_text()
        before, rest = source.split('[candidates]', 1)
        _, fallback = rest.split('[fallback]', 1)
        variants = [
            'candidates = []\n' + before + '[fallback]' + fallback,
            before + '[candidates]\nt1 = []\n[fallback]' + fallback,
            before + '[candidates]\ntypo = "inherit"\n[fallback]' + fallback,
            before + '[candidates]\nt1 = "model:"\n[fallback]' + fallback,
            before + '[candidates]\nt1 = "model: low"\n[fallback]' + fallback,
            source.replace('schema = 1', 'schema = true'),
            source.replace('[budget]', '[budget]\nunknown = true'),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'policy.toml'
            for content in variants:
                with self.subTest(content=content):
                    path.write_text(content)
                    with self.assertRaises(ValueError):
                        load_policy(path)
                    result = subprocess.run([sys.executable, str(ROOT / 'scripts/inspect_cdf_policy.py'),
                                             '--policy', str(path), '--risk', 'LOW'],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(json.loads(result.stdout)['state'], 'error')
                    self.assertNotIn('Traceback', result.stderr)

    def test_direct_resolution_rejects_malformed_candidates(self):
        for candidates in [[], 'inherit', {'t1': 1}, {'typo': 'inherit'}]:
            with self.subTest(candidates=candidates), self.assertRaises(ValueError):
                resolve_child(dict(self.policy, candidates=candidates), role='worker', tier='t1')

    def test_policy_load_and_worker_budget_are_consumed(self):
        policy = load_policy(ROOT / 'policies/model-routing.example.toml')
        self.assertEqual(delegation_decision(policy, risk='LOW', active_workers=2, benefit=True)['mode'], 'DIRECT')
        self.assertEqual(delegation_decision(policy, risk='LOW', active_workers=1, benefit=True)['mode'], 'DELEGATE')
        policy['selected_profile'] = 'budget'
        self.assertEqual(delegation_decision(policy, risk='LOW', active_workers=1, benefit=True)['mode'], 'DIRECT')

    def test_quality_profile_review_and_readiness_override_delegation(self):
        self.policy['selected_profile'] = 'quality'
        decision = delegation_decision(self.policy, risk='MEDIUM', benefit=True, reviewer_available=False, patch_ready=True)
        self.assertTrue(decision['review_required'])
        self.assertEqual(decision['mode'], 'BLOCKED_REVIEW')
        self.assertEqual(delegation_decision(self.policy, risk='LOW', benefit=True, material_questions=True)['mode'], 'WAITING_FOR_USER')

    def test_missing_review_blocks_delivery_but_allows_patch_preparation(self):
        early = delegation_decision(risk='HIGH', benefit=True, reviewer_available=False)
        self.assertEqual(early['mode'], 'DELEGATE')
        self.assertEqual(early['review_gate'], 'BLOCKED_REVIEW')
        self.assertEqual(delegation_decision(risk='HIGH', benefit=True, reviewer_available=False,
                                             patch_ready=True)['mode'], 'BLOCKED_REVIEW')

    def test_cli_exposes_material_and_medium_risk_inputs(self):
        base = [sys.executable, str(ROOT / 'scripts/inspect_cdf_policy.py'), '--policy',
                str(ROOT / 'policies/model-routing.example.toml'), '--risk', 'MEDIUM', '--benefit']
        for flag in ['--shared-contract-changed', '--weak-failure-evidence', '--uncertain-rollback']:
            report = json.loads(subprocess.check_output(base + [flag], text=True))
            self.assertTrue(report['decision']['review_required'])
        report = json.loads(subprocess.check_output(base + ['--material-questions'], text=True))
        self.assertEqual(report['decision']['mode'], 'WAITING_FOR_USER')
        report = json.loads(subprocess.check_output(base + ['--risk', 'HIGH', '--reviewer-unavailable'], text=True))
        self.assertTrue(report['decision']['worker_launch_allowed'])
        self.assertEqual(report['model']['state'], 'fallback')

    def test_selected_fallback_rules_are_enforced(self):
        self.policy['fallback']['when_model_unavailable'] = 'block'
        self.assertEqual(resolve_child(self.policy, role='worker', tier='t1', catalog=set()) .state, 'unavailable')
        self.policy['fallback']['when_model_unavailable'] = 'inherit_with_disclosure'
        self.policy['fallback']['when_effort_unavailable'] = 'block'
        self.assertEqual(resolve_child(self.policy, role='worker', tier='t1',
                                      catalog={('gpt-6.1-terra', 'medium')}).state, 'unavailable')
        self.policy['fallback']['when_effort_unavailable'] = 'guess'
        with self.assertRaises(ValueError):
            resolve_child(self.policy, role='worker', tier='t1')

    def test_confirmed_inheritance_does_not_require_override_support(self):
        pair = ('gpt-6.1-terra', 'low')
        self.policy['fallback']['when_effort_unavailable'] = 'block'
        report = resolve_child(self.policy, role='worker', tier='t1', catalog={pair},
                               inherited=pair, observed=pair, override_supported=False)
        self.assertEqual(report.state, 'confirmed')
        self.assertIsNone(report.requested_model)
        report = resolve_child(self.policy, role='worker', tier='t1', catalog={pair}, override_supported=False)
        self.assertEqual(report.state, 'fallback')

    def test_no_policy_still_limits_workers_and_requires_risk_review(self):
        self.assertFalse(delegation_decision(risk='LOW', active_workers=2, benefit=True)['worker_launch_allowed'])
        self.assertTrue(delegation_decision(risk='MEDIUM', shared_contract_changed=True)['review_required'])
        self.assertTrue(delegation_decision(risk='HIGH')['review_required'])
        self.assertTrue(delegation_decision(risk='LOW', active_workers=2, benefit=True,
                                           authorized_worker_limit=3)['worker_launch_allowed'])

    def test_unsupported_pair_falls_back_without_fabricated_request(self):
        for catalog in [None, {('gpt-6.1-terra', 'medium')}]:
            result = resolve_child(self.policy, role='worker', tier='t1', catalog=catalog, override_supported=True)
            self.assertEqual(result.state, 'fallback')
            self.assertIsNone(result.requested_model)

    def test_explicit_model_requirement_forbids_substitution(self):
        result = resolve_child(self.policy, role='worker', tier='t1', required_pair=('required', 'high'))
        self.assertEqual(result.state, 'unavailable')

    def test_malformed_runtime_evidence_is_rejected(self):
        for kwargs in ({'observed': 'ab'}, {'catalog': {'model': 'effort'}}, {'required_pair': ['only-model']}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                resolve_child(self.policy, role='worker', tier='t1', **kwargs)

    def test_observed_mismatch_is_not_an_unconfirmed_success(self):
        pair = ('gpt-6.1-terra', 'low')
        result = resolve_child(self.policy, role='worker', tier='t1', catalog={pair},
                               override_supported=True, observed=('other', 'high'), required_pair=pair)
        self.assertEqual(result.state, 'unavailable')

    def test_missing_mandatory_reviewer_blocks_even_with_available_model(self):
        result = resolve_child(self.policy, role='cdf_reviewer', tier='t3', reviewer_available=False, review_required=True)
        self.assertEqual(result.state, 'unavailable')
        self.assertIn('BLOCKED_REVIEW', result.reason)


if __name__ == '__main__':
    unittest.main()
