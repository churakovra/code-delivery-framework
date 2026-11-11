"""Offline G5 mechanics. Fake adapters and synthetic snapshots are not model runs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from evals import runner, grade
from evals.conditions import (CANDIDATE_CONDITIONS, HISTORICAL_SHA256, read_snapshot,
                             selected_snapshot, install_snapshot)
from cdf_runtime.contracts import validate_record
from scripts.compare_eval_runs import (analyze, CANDIDATE_CRITICAL, group_parity,
                                      paired_statistics, read_run, improvement_assessment)

ROOT = Path(__file__).resolve().parents[1]


class EngineeringPartnerEvaluations(unittest.TestCase):
    def setUp(self):
        self.tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(self.tmp).resolve()

    def adapter(self, body='print("fake trace")\n'):
        path = self.root / 'adapter'
        path.write_text('#!' + sys.executable + '\n' + body)
        path.chmod(0o755)
        return path

    def legacy(self, update=None):
        data, _ = selected_snapshot('CDF_20')
        data = deepcopy(data)
        data['condition'] = 'LEGACY_CDF_11'
        data['framework_version'] = '1.1.0'
        data['source_revision'] = 'synthetic-test-snapshot'
        data['provenance'] = 'synthetic fixture, not released 1.1.0 bytes'
        if update:
            update(data)
        path = self.root / 'legacy.json'
        path.write_text(json.dumps(data, sort_keys=True))
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def test_historical_snapshot_is_pinned_and_still_has_retired_methods(self):
        snapshot, digest = selected_snapshot('CDF_20')
        self.assertEqual(digest, HISTORICAL_SHA256)
        self.assertEqual(snapshot['framework_version'], '1.0.0')
        self.assertEqual(len(snapshot['core']), 12)
        self.assertIn('.agents/skills/cdf-implementation/SKILL.md', snapshot['files'])
        self.assertNotIn('.agents/skills/cdf/SKILL.md', snapshot['files'])

    def test_legacy_requires_explicit_snapshot_and_hash_before_execution(self):
        adapter = self.adapter('raise AssertionError("must not execute")')
        for path, digest in ((None, None), (self.root / 'missing', 'a' * 64)):
            with self.subTest(path=path), self.assertRaises(ValueError):
                runner.preflight('G03', CANDIDATE_CONDITIONS, adapter, 'external',
                                 legacy_snapshot=path, legacy_sha256=digest)
        self.assertFalse((self.root / 'results').exists())

    def test_invalid_snapshot_hash_version_inventory_path_and_policy(self):
        variants = {
            'version': lambda data: data.update(framework_version='1.0.0'),
            'inventory': lambda data: data['core'].pop(),
            'path': lambda data: data['files'].update({'../secret': 'hostile'}),
            'unknown': lambda data: data['files'].update({'.agents/skills/unknown/SKILL.md': 'hostile'}),
            'case': lambda data: data['files'].update({'.agents/skills/CDF-backend/extra.md': 'hostile'}),
            'policy': lambda data: data.update(agents_block='not a managed block'),
        }
        for name, update in variants.items():
            with self.subTest(name=name):
                path, digest = self.legacy(update)
                with self.assertRaises(ValueError): read_snapshot(path, digest, 'LEGACY_CDF_11')
        path, digest = self.legacy()
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            read_snapshot(path, '0' * 64, 'LEGACY_CDF_11')
        link = self.root / 'link.json'; link.symlink_to(path)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            read_snapshot(link, digest, 'LEGACY_CDF_11')

    def test_snapshot_materialization_preserves_user_policy_and_rejects_collision(self):
        data, _ = selected_snapshot('CDF_20')
        workspace = self.root / 'project'; workspace.mkdir()
        original = b'User policy without newline'
        (workspace / 'AGENTS.md').write_bytes(original)
        install_snapshot(workspace, data)
        self.assertTrue((workspace / 'AGENTS.md').read_bytes().startswith(original + b'\n'))
        with self.assertRaises(ValueError): install_snapshot(workspace, data)

    def test_three_conditions_are_isolated_and_guidance_identities_differ(self):
        path, digest = self.legacy()
        adapter = self.adapter()
        result = runner.run('G03', CANDIDATE_CONDITIONS, adapter, 'external', self.root / 'run',
                            trusted_local_execution=True, legacy_snapshot=path, legacy_sha256=digest)
        self.assertEqual({record['condition'] for record in result}, set(CANDIDATE_CONDITIONS))
        identities = {}
        for record in result:
            folder = self.root / 'run' / record['condition']
            env = json.loads((folder / 'environment.json').read_text())
            identities[record['condition']] = env['guidance_sha256']
            self.assertTrue(env['home_isolated'])
            self.assertFalse(env['credentials_inherited'])
            self.assertEqual(read_run(self.root / 'run', record)['record'], record)
            self.assertNotEqual(record['result'], 'PASS')
        self.assertEqual(len(set(identities.values())), 3)
        snapshot = json.loads((self.root / 'run/LEGACY_CDF_11/environment.json').read_text())['snapshot_identity']
        self.assertEqual(snapshot['sha256'], digest)
        self.assertIn('synthetic', snapshot['provenance'])

    def test_cli_accepts_explicit_three_way_snapshot_flags(self):
        import subprocess
        path, digest = self.legacy()
        adapter = self.adapter()
        command = [sys.executable, str(ROOT / 'scripts/run_cdf_evaluation.py'),
                   '--case', 'G03', '--conditions', *CANDIDATE_CONDITIONS,
                   '--adapter', str(adapter), '--legacy-snapshot', str(path),
                   '--legacy-sha256', digest]
        preview = subprocess.run(command + ['--preflight'], text=True, capture_output=True)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(json.loads(preview.stdout)['conditions'], list(CANDIDATE_CONDITIONS))
        applied = subprocess.run(command + ['--allow-model-runs', '--trusted-local-execution',
                                            '--output', str(self.root / 'cli')],
                                 text=True, capture_output=True)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual(len(json.loads(applied.stdout)), 3)

    def test_candidate_grade_keeps_outcome_separate_from_activation(self):
        adapter = self.adapter("from pathlib import Path\nPath('app.py').write_text(\"def post(body):\\n    if not body: return 400, {'error':'empty body'}\\n    return 200, {'received': body}\\n\")\nprint('fake reviewer evidence')\n")
        runner.run('G01', ['CANDIDATE_CDF'], adapter, 'external', self.root / 'graded',
                   trusted_local_execution=True)
        folder = self.root / 'graded/CANDIDATE_CDF'
        behavior, activation = runner.rubric_names(runner.load_case('G01'), 'CANDIDATE_CDF')
        decisions = {name: {'status': 'FAIL' if name in activation else 'PASS',
                           'reason': 'Synthetic mechanics test annotation, not model evidence.',
                           'evidence': [{'path': 'stdout.ndjson', 'start_line': 1, 'end_line': 1}]}
                     for name in behavior + activation}
        assessment = grade.grade(folder, {'schema': 2, 'rubric_version': 2, 'case_id': 'G01',
                                          'condition': 'CANDIDATE_CDF', 'reviewer': 'test actor',
                                          'assertions': decisions})
        self.assertEqual(assessment['result'], 'PASS')
        self.assertEqual(assessment['activation_result'], 'FAIL')
        self.assertEqual(grade.load_graded(folder)['result'], 'PASS')

    def test_real_artifacts_with_different_timeouts_cannot_match(self):
        path, digest = self.legacy()
        adapter = self.adapter()
        output = self.root / 'timeouts'; output.mkdir()
        case = runner.load_case('G03')
        group = {}; evidence = {}
        for condition, timeout in zip(CANDIDATE_CONDITIONS, (1, 2, 9)):
            record = runner.run_one(case, condition, output, adapter, 'external', 0, timeout,
                                    legacy_snapshot=path, legacy_sha256=digest)
            row = read_run(output, record)
            group[condition] = [row]
            evidence[str(row['folder'].resolve())] = {'runtime': 'v', 'model': 'm', 'effort': 'e',
                                                     'tools': 't', 'permission_mode': 'p',
                                                     'network_policy': 'disabled', 'credentials_policy': 'isolated'}
        self.assertEqual(group_parity(group, evidence), ('MISMATCH', 'timeout_seconds differs'))

    def test_environment_timeout_must_agree_with_command_evidence(self):
        from evals.evidence import write_manifest
        result = runner.run('G03', ['BASE'], self.adapter(), 'external', self.root / 'timeout',
                            timeout=2, trusted_local_execution=True)
        folder = self.root / 'timeout/BASE'
        env = json.loads((folder / 'environment.json').read_text())
        env['timeout_seconds'] = 9
        (folder / 'environment.json').write_text(json.dumps(env))
        (folder / 'evidence-manifest.json').unlink()
        write_manifest(folder)
        with self.assertRaisesRegex(ValueError, 'timeout disagrees'):
            read_run(self.root / 'timeout', result[0])

    def test_candidate_rubric_is_distinct_without_changing_behavior_or_old_hash(self):
        case = runner.load_case('G01')
        original = deepcopy(case)
        historical_behavior, historical_activation = runner.rubric_names(case, 'CDF_20')
        candidate_behavior, candidate_activation = runner.rubric_names(case, 'CANDIDATE_CDF')
        self.assertEqual(historical_behavior, candidate_behavior)
        self.assertIn('activate:cdf-implementation', historical_activation)
        self.assertNotIn('activate:cdf-implementation', candidate_activation)
        self.assertEqual(case, original)
        self.assertEqual(runner.rubric_names(case, 'BASE')[1], [])
        self.assertEqual(runner.rubric_names(case, 'LEGACY_CDF_11')[1], historical_activation)

    def test_candidate_microcase_activation_does_not_require_kernel_in_legacy(self):
        case = runner.load_case('S-CDF-P')
        self.assertIn('activate:cdf', runner.rubric_names(case, 'CANDIDATE_CDF')[1])
        for condition in ('BASE', 'CDF_20', 'LEGACY_CDF_11'):
            self.assertEqual(runner.rubric_names(case, condition)[1], [])

    def test_candidate_overlay_change_invalidates_run(self):
        result = runner.run('G01', ['CANDIDATE_CDF'], self.adapter(), 'external', self.root / 'run',
                            trusted_local_execution=True)
        original = runner.candidate_rubric
        with patch.object(runner, 'candidate_rubric', side_effect=lambda case: dict(original(case), rationale='changed rubric')):
            with self.assertRaisesRegex(ValueError, 'rubric changed'):
                read_run(self.root / 'run', result[0])

    def test_activation_status_is_not_behavior_status_for_new_conditions(self):
        result = runner.run('G03', ['CANDIDATE_CDF'], self.adapter(), 'external', self.root / 'run',
                            trusted_local_execution=True)[0]
        result['acceptance_checks'] = [{'name': 'outcome', 'status': 'PASS'}]
        result['result'] = 'PASS'
        result['activation_checks'] = [{'name': 'activate:cdf', 'status': 'NOT_OBSERVED'}]
        result['activation_result'] = 'NOT_OBSERVED'
        validate_record('eval-run', result)

    def rows(self):
        rows = []; evidence = {}
        for case in CANDIDATE_CRITICAL:
            for condition in CANDIDATE_CONDITIONS:
                folder = self.root / case / condition
                env = {key: value for key, value in (
                    ('case_sha256', case), ('fixture_sha256', case), ('fixture_git_head', case),
                    ('guidance_sha256', condition), ('timeout_seconds', 300))}
                record = {'case_id': case, 'condition': condition, 'seed': 0, 'result': 'PASS',
                          'activation_result': 'NOT_OBSERVED', 'acceptance_checks': [],
                          'resource_measurement': {'basis': 'not_available'}}
                rows.append({'folder': folder, 'record': record, 'environment': env})
                evidence[str(folder.resolve())] = {'runtime': 'v', 'model': 'm', 'effort': 'e',
                                                   'tools': 't', 'permission_mode': 'p',
                                                     'network_policy': 'disabled', 'credentials_policy': 'isolated'}
        return rows, evidence

    def test_three_way_comparison_scores_each_baseline_and_guards_critical_failure(self):
        rows, evidence = self.rows()
        summaries, _, _, _, gate = analyze(rows, evidence)
        self.assertEqual(gate, 'PASS')
        self.assertEqual(set(paired_statistics(summaries)), {'BASE', 'LEGACY_CDF_11'})
        critical = next(row for row in rows if row['record']['condition'] == 'CANDIDATE_CDF'
                        and row['record']['case_id'] == 'E12')
        critical['record']['result'] = 'FAIL'
        self.assertEqual(analyze(rows, evidence)[4], 'FAIL')
        rows.remove(critical)
        self.assertEqual(analyze(rows, evidence)[4], 'BLOCKED')

    def test_improvement_uses_attested_observations_from_actual_runner_shape(self):
        rows, evidence = self.rows()
        for row in rows:
            row['environment'].update(adapter_kind='codex', runtime_version='unverified',
                                      model_observed=None, effort_observed=None)
            row['record']['resource_measurement'] = {'basis': 'observed_runtime'}
            if row['record']['condition'] != 'CANDIDATE_CDF' and row['record']['case_id'] in ('G01', 'G02'):
                row['record']['result'] = 'FAIL'
        summaries, _, _, _, gate = analyze(rows, evidence)
        self.assertEqual(gate, 'PASS')
        self.assertEqual(improvement_assessment(summaries, gate)['overall'], 'PROMISING')
        for row in rows:
            if row['record']['condition'] == 'CANDIDATE_CDF' and row['record']['case_id'] == 'E12':
                row['record']['result'] = 'FAIL'
        summaries, _, _, _, gate = analyze(rows, evidence)
        self.assertEqual(improvement_assessment(summaries, gate)['overall'], 'NEGATIVE')

    def test_policy_attestation_fields_roundtrip_through_hash_bound_evidence(self):
        from scripts.compare_eval_runs import attestations
        path, digest = self.legacy()
        records = runner.run('G03', CANDIDATE_CONDITIONS, self.adapter(), 'external',
                             self.root / 'policies', trusted_local_execution=True,
                             legacy_snapshot=path, legacy_sha256=digest)
        entries = [read_run(self.root / 'policies', record) for record in records]
        items = []
        for entry in entries:
            trace = entry['folder'] / 'stdout.ndjson'
            items.append({'run': str(entry['folder']), 'reviewer': 'test actor',
                          'runtime': 'v', 'model': 'm', 'effort': 'e', 'tools': 't',
                          'permission_mode': 'p', 'network_policy': 'disabled',
                          'credentials_policy': 'isolated', 'evidence': [
                              {'path': 'stdout.ndjson', 'start_line': 1, 'end_line': 1,
                               'sha256': hashlib.sha256(trace.read_bytes()).hexdigest()}]})
        evidence_path = self.root / 'attestations.json'
        evidence_path.write_text(json.dumps({'schema': 1, 'runs': items}))
        parsed = attestations(evidence_path, entries)
        self.assertTrue(all(item['network_policy'] == 'disabled' for item in parsed.values()))
        group = {entry['record']['condition']: [entry] for entry in entries}
        self.assertEqual(group_parity(group, parsed)[0], 'MATCHED_ATTESTED')
        del items[0]['credentials_policy']
        evidence_path.write_text(json.dumps({'schema': 1, 'runs': items}))
        self.assertEqual(group_parity(group, attestations(evidence_path, entries))[0], 'UNVERIFIED')

    def test_new_triple_requires_equal_network_and_credentials_policy_attestations(self):
        for field in ('network_policy', 'credentials_policy'):
            with self.subTest(field=field):
                rows, evidence = self.rows()
                group = {row['record']['condition']: [row] for row in rows[:3]}
                key = str(rows[0]['folder'].resolve())
                saved = evidence[key].pop(field)
                self.assertEqual(group_parity(group, evidence),
                                 ('UNVERIFIED', f'{field} attestation unavailable'))
                self.assertEqual(analyze(rows, evidence)[4], 'BLOCKED')
                evidence[key][field] = 'different policy'
                self.assertEqual(group_parity(group, evidence), ('MISMATCH', f'{field} differs'))
                evidence[key][field] = saved
                self.assertEqual(group_parity(group, evidence)[0], 'MATCHED_ATTESTED')

    def test_historical_pair_cannot_fill_missing_candidate_critical_case(self):
        rows, evidence = self.rows()
        case = CANDIDATE_CRITICAL[0]
        rows[:] = [row for row in rows if row['record']['case_id'] != case]
        for condition in ('BASE', 'CDF_20'):
            folder = self.root / case / condition
            row = {'folder': folder, 'record': {'case_id': case, 'condition': condition,
                   'seed': 0, 'result': 'PASS', 'activation_result': 'PASS'},
                   'environment': {'case_sha256': case, 'fixture_sha256': case,
                                   'fixture_git_head': case, 'guidance_sha256': condition}}
            rows.append(row)
            evidence[str(folder.resolve())] = {'runtime': 'v', 'model': 'm', 'effort': 'e',
                                               'tools': 't', 'permission_mode': 'p',
                                                     'network_policy': 'disabled', 'credentials_policy': 'isolated'}
        self.assertEqual(analyze(rows, evidence)[4], 'BLOCKED')

    def test_archived_historical_record_without_snapshot_metadata_remains_readable(self):
        from evals.evidence import write_manifest
        records = runner.run('G03', ['CDF_20'], self.adapter(), 'external', self.root / 'old',
                             trusted_local_execution=True)
        folder = self.root / 'old/CDF_20'
        env = json.loads((folder / 'environment.json').read_text())
        del env['snapshot_identity']
        del env['activation_rubric_sha256']
        (folder / 'environment.json').write_text(json.dumps(env))
        (folder / 'guidance-snapshot.json').unlink()
        (folder / 'evidence-manifest.json').unlink()
        write_manifest(folder)
        self.assertEqual(read_run(self.root / 'old', records[0])['record'], records[0])

    def test_changing_guidance_or_missing_condition_prevents_matched_gate(self):
        rows, evidence = self.rows()
        rows[-1]['environment']['guidance_sha256'] = 'changed'
        self.assertEqual(analyze(rows, evidence)[4], 'BLOCKED')
        group = {row['record']['condition']: [row] for row in rows[:3]}
        group.pop('LEGACY_CDF_11')
        self.assertEqual(group_parity(group, evidence)[0], 'UNVERIFIED')

    def feedback(self, outputs, turns=2, initial=None):
        folder = self.root / 'feedback'; (folder / 'turns').mkdir(parents=True)
        workspace = self.root / 'workspace'; workspace.mkdir()
        if initial is None:
            initial = ('completed', 0, b'{"type":"thread.started","thread_id":"9f227fe2-04a5-4d45-b073-49666d4745ae"}\n', b'', 0)
        feedback = [{'message': f'Correction {i}', 'check': 'checks/G28.py'} for i in range(turns)]
        with patch.object(runner, '_process', side_effect=outputs) as process:
            result, _ = runner._native_feedback(Path('/fake'), workspace, {}, folder, initial,
                                                feedback, 10, None, None, {})
        return json.loads((folder / 'feedback.json').read_text()), result, process, folder

    def test_initial_success_requires_no_corrective_turn_or_thread_id(self):
        summary, result, process, folder = self.feedback([('completed', 0, b'', b'', 0)],
                                                        initial=('completed', 0, b'', b'', 0))
        self.assertEqual(summary['status'], 'NOT_REQUIRED')
        self.assertEqual(summary['delivered'], 0)
        self.assertEqual(process.call_count, 1)
        self.assertFalse((folder / 'turns/1.feedback.stdin.txt').exists())
        self.assertEqual(result[0], 'completed')

    def test_first_repair_success_does_not_deliver_later_feedback(self):
        summary, _, process, folder = self.feedback([
            ('completed', 42, b'', b'', 0), ('completed', 0, b'fixed', b'', 0),
            ('completed', 0, b'', b'', 0)])
        self.assertEqual(summary['status'], 'RESOLVED_EARLY')
        self.assertEqual(summary['delivered'], 1)
        self.assertTrue(summary['resolved'])
        self.assertEqual(process.call_count, 3)
        self.assertFalse((folder / 'turns/2.feedback.stdin.txt').exists())

    def test_second_correction_has_final_observation(self):
        summary, _, process, _ = self.feedback([
            ('completed', 42, b'', b'', 0), ('completed', 0, b'not fixed', b'', 0),
            ('completed', 42, b'', b'', 0), ('completed', 0, b'fixed', b'', 0),
            ('completed', 0, b'', b'', 0)])
        self.assertEqual(summary['status'], 'CORRECTION_COMPLETED')
        self.assertEqual(summary['delivered'], 2)
        self.assertEqual(len(summary['observations']), 3)
        self.assertTrue(summary['resolved'])
        self.assertEqual(process.call_count, 5)

    def test_oracle_error_is_runner_error_not_product_failure(self):
        summary, result, _, _ = self.feedback([('completed', 1, b'', b'exception', 0)])
        self.assertEqual(summary['status'], 'ORACLE_ERROR')
        self.assertEqual(result[0], 'runner-error')

    def test_missing_thread_or_failed_resume_is_warranted_not_delivered(self):
        for mode in ('missing', 'failed'):
            with self.subTest(mode=mode):
                # Each call uses its own isolated directories.
                with tempfile.TemporaryDirectory() as folder:
                    old = self.root; self.root = Path(folder)
                    try:
                        outputs = [('completed', 42, b'', b'', 0)]
                        initial = ('completed', 0, b'no thread', b'', 0) if mode == 'missing' else None
                        if mode == 'failed': outputs.append(('completed', 1, b'', b'failed resume', 0))
                        summary, result, _, _ = self.feedback(outputs, initial=initial)
                        self.assertEqual(summary['status'], 'WARRANTED_NOT_DELIVERED')
                        self.assertEqual(summary['delivered'], 0)
                        self.assertTrue(result[0] != 'completed' or result[1] != 0)
                    finally:
                        self.root = old


if __name__ == '__main__':
    unittest.main()
