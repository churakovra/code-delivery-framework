"""Offline metric regression tests; synthetic rows never represent live trials."""
from copy import deepcopy
import json
import unittest

from evals.runner import _trace_metrics
from scripts.compare_eval_runs import improvement_assessment


class OutcomeMetricsTests(unittest.TestCase):
    def trace(self, *events):
        return ('\n'.join(json.dumps(e) for e in events) + '\n').encode()

    def test_complete_zero_one_and_unknown_command_counts(self):
        terminal = {'type': 'turn.completed'}
        command = {'type': 'item.completed', 'item': {'type': 'command_execution'}}
        self.assertEqual(_trace_metrics(self.trace(terminal), 'codex'), 0)
        self.assertEqual(_trace_metrics(self.trace(command, terminal), 'codex'), 1)
        self.assertIsNone(_trace_metrics(self.trace(command), 'codex'))
        self.assertIsNone(_trace_metrics(self.trace(terminal, {'type': 'turn.started'}), 'codex'))
        for malformed in (b'no json', b'[]\n', b'\xff', self.trace({}, terminal),
                          self.trace({'type': 'item.completed'}, terminal),
                          self.trace({'type': 'item.completed', 'item': {}}, terminal),
                          self.trace({'type': 'item.completed', 'item': {'type': ''}}, terminal)):
            self.assertIsNone(_trace_metrics(malformed, 'codex'))
        self.assertIsNone(_trace_metrics(self.trace(terminal), 'external'))

    def summaries(self):
        rows = []
        for n in range(5):
            group = {}
            for condition in ('BASE', 'LEGACY_CDF_11', 'CANDIDATE_CDF'):
                group[condition] = [{
                    'record': {'result': 'PASS', 'resource_measurement': {'basis': 'observed_runtime'}},
                    'environment': {'adapter_kind': 'codex', 'runtime_version': 'test-runtime',
                                    'model_observed': 'test-model', 'effort_observed': 'test-effort'}}]
            rows.append({'case_id': f'test-{n}', 'parity': 'MATCHED_ATTESTED', 'group': group})
        return rows

    def wins(self, rows):
        for row in rows[:2]:
            for name in ('BASE', 'LEGACY_CDF_11'):
                row['group'][name][0]['record']['result'] = 'FAIL'

    def test_equal_passes_do_not_prove_improvement(self):
        self.assertEqual(improvement_assessment(self.summaries(), 'PASS')['overall'], 'NOT_PROVEN')

    def test_matched_signal_is_separate_from_quality_and_each_baseline(self):
        rows = self.summaries(); self.wins(rows)
        self.assertEqual(improvement_assessment(rows, 'PASS')['overall'], 'PROMISING')
        self.assertEqual(improvement_assessment(rows, 'BLOCKED')['overall'], 'NOT_PROVEN')
        rows[0]['group']['LEGACY_CDF_11'][0]['record']['result'] = 'PASS'
        self.assertEqual(improvement_assessment(rows, 'PASS')['against']['LEGACY_CDF_11'], 'NOT_PROVEN')

    def test_unknown_synthetic_unmatched_and_repeated_case_cannot_prove_gains(self):
        original = self.summaries(); self.wins(original)
        for mutate in (
            lambda rows: rows[0].update(parity='UNVERIFIED'),
            lambda rows: rows[0]['group'].pop('BASE'),
            lambda rows: rows[0]['group']['BASE'][0]['record'].update(result='NOT_OBSERVED'),
            lambda rows: rows[0]['group']['BASE'][0]['record']['resource_measurement'].update(basis='not_available'),
            lambda rows: rows[0]['group']['BASE'][0]['environment'].update(adapter_kind='fake'),
            lambda rows: rows[0]['group']['BASE'][0]['environment'].update(model_observed='unverified'),
            lambda rows: [row.update(case_id='same-case') for row in rows],
        ):
            rows = deepcopy(original); mutate(rows)
            self.assertEqual(improvement_assessment(rows, 'PASS')['overall'], 'NOT_PROVEN')

    def test_observed_regression_is_negative(self):
        rows = self.summaries(); self.wins(rows)
        rows[-1]['group']['CANDIDATE_CDF'][0]['record']['result'] = 'FAIL'
        self.assertEqual(improvement_assessment(rows, 'FAIL')['overall'], 'NEGATIVE')

    def test_progress_requires_reviewed_evidence_and_keeps_host_rendering_unknown(self):
        from scripts.compare_eval_runs import progress_observations
        record = {'acceptance_checks': [
            {'name': name, 'status': 'PASS', 'evidence_refs': [{'path': 'stdout.ndjson'}]}
            for name in ('progress_update_emitted', 'progress_statement_supported',
                         'status_chatter_count_zero', 'status_false_success_absent')]}
        measured = progress_observations(record)
        self.assertIs(measured['progress_update_emitted'], True)
        self.assertIsNone(measured['progress_update_rendered'])
        self.assertIs(measured['progress_statement_supported'], True)
        self.assertEqual(measured['status_chatter_count'], 0)
        self.assertIs(measured['status_false_success'], False)
        record['acceptance_checks'][-1]['status'] = 'FAIL'
        record['acceptance_checks'][-2]['status'] = 'FAIL'
        measured = progress_observations(record)
        self.assertIs(measured['status_false_success'], True)
        self.assertIsNone(measured['status_chatter_count'])
        for check in record['acceptance_checks']:
            check.pop('evidence_refs')
        self.assertTrue(all(value is None for value in progress_observations(record).values()))
