"""Model-free regression tests for the CDF 2.0 evaluation runner."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from evals import runner
from evals import grade

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts' / 'run_cdf_evaluation.py'
COMPARE = ROOT / 'scripts' / 'compare_eval_runs.py'


class CDFEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cdf-eval-tests-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def adapter(self, body):
        path = self.root / 'adapter.py'
        path.write_text('#!'+sys.executable+'\n'+body)
        path.chmod(0o755)
        return path

    def invoke(self, adapter, *args, case='G01', conditions=('BASE',)):
        return subprocess.run([sys.executable, str(CLI), '--adapter', str(adapter), '--case', case,
                               '--conditions', *conditions, *(['--trusted-local-execution'] if '--allow-model-runs' in args else []), *args], capture_output=True, text=True)

    def test_feedback_real_oracle_and_fake_cli_end_to_end(self):
        for mode in ('repair', 'resolved', 'exception'):
            with self.subTest(mode=mode):
                folder = self.root / mode; folder.mkdir()
                adapter = folder / 'adapter.py'
                body = "import json,sys\nfrom pathlib import Path\nthread='9f227fe2-04a5-4d45-b073-49666d4745ae'\n"
                body += "text=sys.stdin.read()\n"
                body += "if sys.argv[1:3]==['exec','resume']:\n assert sys.argv[3]==thread\n Path('app.py').write_text(\"def preview(): return 'hello'\\nspacing=12\\n\")\n"
                if mode == 'resolved':
                    body += "else:\n Path('app.py').write_text(\"def preview(): return 'hello'\\nspacing=12\\n\")\n"
                elif mode == 'exception':
                    body += "else:\n Path('app.py').write_text('syntax error!')\n"
                body += "print(json.dumps({'type':'thread.started','thread_id':thread}))\nprint(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Done.'}}))\n"
                adapter.write_text('#!' + sys.executable + '\n' + body); adapter.chmod(0o755)
                case = runner.load_case('G28')
                runner.run_one(case, 'BASE', folder, adapter, 'codex', 0, 10)
                run = folder / 'BASE'
                observation = json.loads((run/'turns/1.feedback.observation.json').read_text())
                record = json.loads((run/'run.json').read_text())
                if mode == 'repair':
                    self.assertTrue(observation['warranted'])
                    self.assertTrue((run/'turns/1.feedback.stdin.txt').exists())
                    self.assertFalse((run/'turns/2.feedback.stdin.txt').exists())
                else:
                    self.assertFalse((run/'turns/1.feedback.stdin.txt').exists())
                if mode == 'exception': self.assertEqual(record['result'], 'RUNNER_ERROR')
                from evals.evidence import verify_manifest
                verify_manifest(run)

    def test_native_feedback_observes_before_delivering_without_question(self):
        folder = self.root / 'feedback'; (folder / 'turns').mkdir(parents=True)
        workspace = self.root / 'workspace'; workspace.mkdir()
        initial = ('completed', 0, b'{"type":"thread.started","thread_id":"9f227fe2-04a5-4d45-b073-49666d4745ae"}\n', b'', 0)
        turn = {'message': 'Still wrong.', 'check': 'checks/G28.py'}
        observation = ('completed', 42, b'', b'', 0)
        resumed = ('completed', 0, b'fixed', b'', 0)
        with mock.patch.object(runner, '_process', side_effect=[observation, resumed]) as process:
            result, outputs = runner._native_feedback(Path('/adapter'), workspace, {}, folder, initial, [turn], 10, None, None, {})
        self.assertEqual(result[0], 'completed')
        self.assertEqual(process.call_args_list[1].args[0][3], '9f227fe2-04a5-4d45-b073-49666d4745ae')
        self.assertEqual(len(outputs), 2)
        self.assertTrue(json.loads((folder/'turns/1.feedback.observation.json').read_text())['warranted'])

    def test_native_feedback_withholds_resolved_and_rejects_oracle_error(self):
        for exit_code, expected in [(0, 'completed'), (1, 'runner-error')]:
            with self.subTest(exit_code=exit_code):
                folder = self.root / str(exit_code); (folder/'turns').mkdir(parents=True)
                initial = ('completed', 0, b'{"type":"thread.started","thread_id":"9f227fe2-04a5-4d45-b073-49666d4745ae"}\n', b'', 0)
                with mock.patch.object(runner, '_process', return_value=('completed', exit_code, b'', b'', 0)) as process:
                    result, _ = runner._native_feedback(Path('/adapter'), self.root, {}, folder, initial, [{'message':'Still wrong', 'check':'checks/G28.py'}], 10, None, None, {})
                self.assertEqual(result[0], expected)
                self.assertEqual(process.call_count, 1)
                self.assertFalse((folder/'turns/1.feedback.stdin.txt').exists())

    def test_feedback_contract_is_bounded_and_external_rejected(self):
        with self.assertRaises(ValueError): runner._feedback_turns({'feedback_turns': [{}] * 5})
        with self.assertRaises(ValueError): runner._feedback_turns({'feedback_turns': [{'message':'x','check':'../runner.py'}]})
        adapter = self.adapter('print("unused")')
        with self.assertRaisesRegex(ValueError, 'native Codex'):
            runner.preflight('G28', ['BASE'], adapter, 'external')

    def test_manifest_detects_unreferenced_trace_and_usage_tampering(self):
        from evals.evidence import write_manifest
        from scripts.compare_eval_runs import read_run
        adapter = self.adapter('print("trace")\n')
        result = self.invoke(adapter, '--output', str(self.root/'r'), '--allow-model-runs', case='G03')
        self.assertEqual(result.returncode, 0, result.stderr)
        folder = self.root/'r'/'BASE'
        record = json.loads((folder/'run.json').read_text())
        (folder/'stdout.ndjson').write_text('changed trace\n')
        with self.assertRaisesRegex(ValueError, 'manifest mismatch'):
            read_run(self.root/'r', record)
        # Rebuilding a consistency manifest cannot make recorded usage agree with stdout.
        record['resource_measurement']['input_tokens'] = 999
        (folder/'run.json').write_text(json.dumps(record))
        (folder/'evidence-manifest.json').unlink()
        write_manifest(folder)
        with self.assertRaisesRegex(ValueError, 'Resource measurement'):
            read_run(self.root/'r', record)

    def test_git_config_mutation_is_detected(self):
        adapter = self.adapter("from pathlib import Path\nPath('.git/config').write_text('changed')\n")
        result = self.invoke(adapter, '--output', str(self.root/'r'), '--allow-model-runs', case='G03')
        record = json.loads((self.root/'r'/'BASE'/'run.json').read_text())
        check = next(c for c in record['acceptance_checks'] if c['name'] == 'git_policy_metadata_unchanged')
        self.assertEqual(check['status'], 'FAIL')

    def test_comparison_regime_allows_only_attested_tool_differences(self):
        from scripts.compare_eval_runs import group_parity
        group = {}; evidence = {}
        for condition in runner.CONDITIONS:
            folder = self.root/condition
            group[condition] = [{'folder': folder, 'environment': {
                'case_sha256':'a', 'fixture_sha256':'b', 'fixture_git_head':'c',
                'guidance_sha256': condition}}]
            evidence[str(folder.resolve())] = {'runtime':'v', 'model':'m', 'effort':'e',
                'permission_mode':'p', 'tools': condition}
        self.assertEqual(group_parity(group, evidence)[0], 'MISMATCH')
        self.assertEqual(group_parity(group, evidence, 'installed-system')[0], 'MATCHED_ATTESTED')
        evidence.pop(str((self.root/'BASE').resolve()))
        self.assertEqual(group_parity(group, evidence, 'installed-system')[0], 'UNVERIFIED')

    def test_partial_runner_error_preserves_trace_and_is_comparable(self):
        from scripts.compare_eval_runs import read_run
        adapter = self.adapter('print("partial output")\n')
        save_json = runner._json
        def fail_after_trace(path, value):
            if path.name == 'workspace-after.json': raise OSError('injected failure')
            return save_json(path, value)
        with mock.patch.object(runner, '_json', side_effect=fail_after_trace):
            records = runner.run('G03', ['BASE'], adapter, 'external', self.root/'partial',
                                 trusted_local_execution=True)
        folder = self.root/'partial'/'BASE'
        self.assertEqual((folder/'stdout.ndjson').read_text(), 'partial output\n')
        self.assertIsNotNone(records[0]['resource_measurement']['elapsed_seconds'])
        self.assertEqual(read_run(self.root/'partial', records[0])['record']['result'], 'RUNNER_ERROR')

    def test_late_runner_error_never_emits_contradictory_summary(self):
        adapter = self.adapter('print("trace")\n')
        save_json = runner._json
        def fail_after_record(path, value):
            if path.name == 'score.json': raise OSError('injected failure')
            return save_json(path, value)
        with mock.patch.object(runner, '_json', side_effect=fail_after_record):
            with self.assertRaisesRegex(RuntimeError, 'Incomplete run after record'):
                runner.run('G03', ['BASE'], adapter, 'external', self.root/'late',
                           trusted_local_execution=True)
        self.assertTrue((self.root/'late'/'BASE'/'run.json').is_file())
        self.assertFalse((self.root/'late'/'results.json').exists())

    def test_malformed_evidence_manifests_fail_cleanly(self):
        from evals.evidence import verify_manifest, verify_grade_manifest
        folder = self.root/'evidence'; folder.mkdir()
        for malformed in (None, [], {'schema': True, 'algorithm': 'sha256', 'files': {}}):
            (folder/'evidence-manifest.json').write_text(json.dumps(malformed))
            with self.assertRaises(ValueError): verify_manifest(folder)
        (folder/'grade-manifest.json').write_text(json.dumps({'schema': True, 'files': {}}))
        with self.assertRaises(ValueError): verify_grade_manifest(folder)
        (folder/'grade-manifest.json').write_text(json.dumps({'schema': 1, 'files': {}}))
        (folder/'grading.json').symlink_to(folder/'evidence-manifest.json')
        with self.assertRaisesRegex(ValueError, 'Symlink'): verify_grade_manifest(folder)

    def test_all_cases_have_fixture_and_checks_are_external(self):
        data = json.loads((ROOT/'evals/golden-cases.json').read_text())
        self.assertEqual(len({x['id'] for x in data['cases']}), 31)
        for case in data['cases']:
            with self.subTest(case=case['id']):
                fixture = ROOT/'evals'/case['fixture']
                self.assertTrue(fixture.is_dir())
                self.assertTrue(any(fixture.iterdir()))
                if case['deterministic_check']:
                    self.assertTrue((ROOT/'evals'/case['deterministic_check']).is_file())
                    self.assertNotIn('checks/', case['prompt'])
                self.assertTrue(case['must'])
                self.assertTrue(case['must_not'])

    def test_preflight_is_read_only_and_does_not_run_adapter(self):
        sentinel = self.root/'ran'
        adapter = self.adapter(f'from pathlib import Path\nPath({str(sentinel)!r}).touch()\n')
        result = self.invoke(adapter, '--preflight')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(sentinel.exists())
        self.assertEqual(json.loads(result.stdout)['runtime_version'], 'unverified')

    def test_explicit_opt_in_required(self):
        adapter = self.adapter('raise SystemExit(0)\n')
        result = self.invoke(adapter, '--output', str(self.root/'out'))
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root/'out').exists())

    def test_live_execution_requires_trusted_local_opt_in(self):
        sentinel = self.root/'ran'
        adapter = self.adapter(f'from pathlib import Path\nPath({str(sentinel)!r}).touch()\n')
        result = subprocess.run([sys.executable, str(CLI), '--adapter', str(adapter), '--case', 'G03',
                                 '--conditions', 'BASE', '--output', str(self.root/'out'),
                                 '--allow-model-runs'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(sentinel.exists())
        self.assertFalse((self.root/'out').exists())

    def test_two_conditions_isolate_home_and_preserve_truthful_results(self):
        adapter = self.adapter('''import os, sys
from pathlib import Path
assert 'CDF_EVAL_TEST_SECRET' not in os.environ
assert Path(os.environ['HOME']).name == 'home'
assert Path(os.environ['CODEX_HOME']).parent == Path(os.environ['HOME'])
assert not Path(os.environ['HOME'], 'marker').exists()
Path(os.environ['HOME'], 'marker').write_text('x')
prompt=sys.stdin.read()
assert 'checks/G01' not in prompt
Path('app.py').write_text("def post(body):\\n    if not body: return 400, {'error':'empty body'}\\n    return 200, {'received': body}\\n")
print('{"fake":true}')
''')
        result = subprocess.run([sys.executable,str(CLI),'--adapter',str(adapter),'--case','G01',
                                 '--output',str(self.root/'results'),'--allow-model-runs','--trusted-local-execution'],
                                env=dict(os.environ, CDF_EVAL_TEST_SECRET='private'), capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        records=json.loads(result.stdout)
        self.assertEqual({r['condition'] for r in records}, set(runner.CONDITIONS))
        self.assertTrue(all(r['result']=='NOT_OBSERVED' for r in records))
        hashes=set()
        for record in records:
            folder=self.root/'results'/record['condition']
            hashes.add((folder/'initial_sha.txt').read_text())
            self.assertEqual(record['resource_measurement']['basis'],'not_available')
            self.assertIsNone(record['model_observed'])
            self.assertTrue(any(c['name']=='fixture_behavior' and c['status']=='PASS' for c in record['acceptance_checks']))
            self.assertTrue(any(c['status']=='NOT_OBSERVED' for c in record['acceptance_checks']))
            self.assertIn('def post', (folder/'final.diff').read_text())
        self.assertEqual(len(hashes),1)
        self.assertEqual(len({json.loads((self.root/'results'/r['condition']/'environment.json').read_text())['fixture_git_head'] for r in records}),1)
        again=self.invoke(adapter,'--output',str(self.root/'results'),'--allow-model-runs')
        self.assertEqual(again.returncode,2)

    def test_nonzero_adapter_does_not_score_behavior_pass(self):
        adapter=self.adapter('import sys\nprint("broken",file=sys.stderr)\nsys.exit(7)\n')
        result=self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs')
        self.assertEqual(result.returncode,1,result.stderr)
        rec=json.loads((self.root/'r'/'BASE'/'run.json').read_text())
        self.assertEqual(rec['result'],'RUNNER_ERROR')
        self.assertEqual(next(c for c in rec['acceptance_checks'] if c['name']=='fixture_behavior')['status'],'NOT_OBSERVED')
        self.assertIn('broken',(self.root/'r'/'BASE'/'stderr.txt').read_text())

    def test_failing_behavior_is_not_confused_with_successful_adapter(self):
        adapter=self.adapter('print("ok")\n')
        result=self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs')
        self.assertEqual(result.returncode,1)
        rec=json.loads((self.root/'r'/'BASE'/'run.json').read_text())
        self.assertEqual(rec['result'],'FAIL')
        self.assertEqual(next(c for c in rec['acceptance_checks'] if c['name']=='fixture_behavior')['status'],'FAIL')

    def test_timeout_records_partial_output(self):
        adapter=self.adapter('import time\nprint("started",flush=True)\ntime.sleep(10)\n')
        result=self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs','--timeout','1')
        self.assertEqual(result.returncode,1)
        score=json.loads((self.root/'r'/'BASE'/'score.json').read_text())
        self.assertEqual(score['adapter_state'],'timeout')
        self.assertIn('started',(self.root/'r'/'BASE'/'stdout.ndjson').read_text())

    def test_exploratory_case_rejects_new_workspace_file(self):
        adapter=self.adapter("from pathlib import Path\nPath('unrequested.py').write_text('x=1')\n")
        result=self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs',case='G03')
        self.assertEqual(result.returncode,1)
        rec=json.loads((self.root/'r'/'BASE'/'run.json').read_text())
        self.assertEqual(rec['result'],'FAIL')

    def test_exploratory_case_detects_mode_change_and_empty_directory(self):
        adapter=self.adapter('''from pathlib import Path
import stat
path=Path('app.py')
old=stat.S_IMODE(path.stat().st_mode)
path.chmod(0o700 if old == 0o777 else 0o777)
Path('new-empty-dir').mkdir()
''')
        result=self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs',case='G03')
        self.assertEqual(result.returncode,1,result.stderr)
        folder=self.root/'r'/'BASE'
        rec=json.loads((folder/'run.json').read_text())
        self.assertEqual(next(c for c in rec['acceptance_checks'] if c['name']=='fixture_source_unchanged')['status'],'FAIL')
        before=json.loads((folder/'workspace-before.json').read_text())
        after=json.loads((folder/'workspace-after.json').read_text())
        self.assertNotEqual(before['app.py']['mode'],after['app.py']['mode'])
        self.assertNotIn('new-empty-dir',before)
        self.assertEqual(after['new-empty-dir']['type'],'directory')
        diff=(folder/'final.diff').read_text()
        self.assertIn('app.py: mode ',diff)
        self.assertIn('new-empty-dir: absent -> directory',diff)
        snapshot=runner._snapshot(ROOT/'evals'/'fixtures'/'G03')
        changed=dict(snapshot)
        kind, data, mode=changed['app.py']
        changed['app.py']=(kind,data,mode ^ 0o100)
        self.assertNotEqual(runner._hash_snapshot(snapshot),runner._hash_snapshot(changed))

    def test_scripted_answers_require_explicit_external_dialogue_protocol(self):
        adapter=self.adapter('''import json, sys
request=json.load(sys.stdin)
assert request['schema'] == 1
assert request['prompt'] == 'Initial question only.'
assert request['scripted_answers'] == ['Answer after agent question.']
assert 'Answer after agent question.' not in request['prompt']
print('adapter received separated answers')
''')
        case=dict(runner.load_case('G03'), prompt='Initial question only.',
                  scripted_answers=['Answer after agent question.'])
        capabilities={'schema':1,'protocols':['json-dialogue-v1'],'multi_turn':True,'runtime_controls':[]}
        with mock.patch.object(runner,'load_case',return_value=case):
            with self.assertRaisesRegex(ValueError, 'requires an external'):
                runner.preflight('G03',['BASE'],adapter,'external')
            with self.assertRaisesRegex(ValueError, 'does not implement'):
                runner.preflight('G03',['BASE'],adapter,'codex','json-dialogue-v1')
            result=runner.preflight('G03',['BASE'],adapter,'external','json-dialogue-v1',capabilities)
            self.assertEqual(result['dialogue_capability'],'operator_asserted_unverified')
            records=runner.run('G03',['BASE'],adapter,'external',self.root/'dialogue',trusted_local_execution=True,
                               timeout=5,protocol='json-dialogue-v1',declared_capabilities=capabilities)
        self.assertEqual(records[0]['result'],'NOT_OBSERVED')
        folder=self.root/'dialogue'/'BASE'
        request=json.loads((folder/'dialogue-request.json').read_text())
        self.assertEqual(request['scripted_answers'],case['scripted_answers'])
        self.assertEqual((folder/'prompt.txt').read_text(),'Initial question only.\n')
        self.assertEqual(json.loads((folder/'environment.json').read_text())['dialogue_capability'],'operator_asserted_unverified')

    def test_dirty_tree_is_real_and_staging_is_detected(self):
        adapter=self.adapter('''from pathlib import Path
import subprocess
status=subprocess.run(['git','status','--porcelain'],capture_output=True,text=True,check=True).stdout
assert 'notes.txt' in status
Path('app.py').write_text('def response(value): return 200, value\\n')
subprocess.run(['git','add','app.py'],check=True)
''')
        result=self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs',case='G14')
        self.assertEqual(result.returncode,1,result.stderr)
        rec=json.loads((self.root/'r'/'BASE'/'run.json').read_text())
        self.assertEqual(next(c for c in rec['acceptance_checks'] if c['name']=='git_head_branch_and_index_unchanged')['status'],'FAIL')
        self.assertEqual(next(c for c in rec['acceptance_checks'] if c['name']=='fixture_behavior')['status'],'PASS')

    def test_compare_reports_unknown_and_does_not_overwrite_csv(self):
        adapter=self.adapter("from pathlib import Path\nPath('app.py').write_text(\"def post(body):\\n    if not body: return 400, {'error':'empty body'}\\n    return 200, {'received': body}\\n\")\n")
        self.assertEqual(self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs').returncode,0)
        csv=self.root/'summary.csv'
        cmd=[sys.executable,str(COMPARE),str(self.root/'r'),'--csv',str(csv)]
        p=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('NOT_OBSERVED',p.stdout)
        self.assertIn('NOT_OBSERVED',csv.read_text())
        self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)

    def test_codex_version_effort_and_documented_turn_usage(self):
        adapter=self.adapter('''import json, sys
from pathlib import Path
if sys.argv[1:] == ['--version']:
    print('codex fake-1'); raise SystemExit(0)
assert '--json' in sys.argv
assert 'model_reasoning_effort="medium"' in sys.argv
assert '--model' in sys.argv
Path('app.py').write_text("def post(body):\\n    if not body: return 400, {'error':'empty body'}\\n    return 200, {'received': body}\\n")
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':3}}))
''')
        result=self.invoke(adapter,'--adapter-kind','codex','--model','candidate','--effort','medium',
                           '--output',str(self.root/'r'),'--allow-model-runs')
        self.assertEqual(result.returncode,0,result.stderr)
        rec=json.loads((self.root/'r'/'BASE'/'run.json').read_text())
        env=json.loads((self.root/'r'/'BASE'/'environment.json').read_text())
        self.assertEqual(rec['runtime_version'],'codex fake-1')
        self.assertEqual(rec['resource_measurement']['input_tokens'],10)
        self.assertEqual(rec['resource_measurement']['output_tokens'],3)
        self.assertEqual(rec['resource_measurement']['basis'],'observed_runtime')
        self.assertEqual(env['effort_requested'],'medium')
        self.assertIsNone(env['effort_observed'])
        self.assertIsNone(rec['model_observed'])
        self.assertEqual(len(env['guidance_sha256']),64)

    def test_unknown_or_malformed_usage_remains_unavailable(self):
        self.assertEqual(runner._usage(b'{bad', 'codex', 1)['basis'], 'not_available')
        self.assertEqual(runner._usage(b'{"type":"turn.completed","usage":{"input_tokens":3}}', 'codex', 1)['basis'], 'not_available')
        self.assertEqual(runner._usage(b'{"type":"other","usage":{"input_tokens":3,"output_tokens":2}}', 'codex', 1)['basis'], 'not_available')

    def test_grading_needs_complete_decisions_and_cited_evidence(self):
        adapter=self.adapter("from pathlib import Path\nPath('app.py').write_text(\"def post(body):\\n    if not body: return 400, {'error':'empty body'}\\n    return 200, {'received': body}\\n\")\nprint('trace')\n")
        self.assertEqual(self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs').returncode,0)
        folder=self.root/'r'/'BASE'
        case=runner.load_case('G01')
        names=sum(runner.rubric_names(case, 'BASE'), [])
        decisions={name:{'status':'PASS','reason':'Reviewed trace and check.',
                         'evidence':[{'path':'stdout.ndjson','start_line':1,'end_line':1}]}
                   for name in names}
        data={'schema':2,'rubric_version':runner.RUBRIC_VERSION,'case_id':'G01','condition':'BASE','reviewer':'reviewer', 'assertions':decisions}
        missing=dict(data,assertions={})
        with self.assertRaises(ValueError): grade.grade(folder,missing)
        bad=json.loads(json.dumps(data)); bad['assertions'][names[0]]['evidence'][0]['path']='../../outside'
        with self.assertRaises(ValueError): grade.grade(folder,bad)
        outcome=grade.grade(folder,data)
        self.assertEqual(outcome['result'],'PASS')
        self.assertEqual(grade.load_graded(folder)['result'],'PASS')
        grading_path = folder/'grading.json'
        grading_bytes = grading_path.read_bytes()
        grading_path.write_bytes(grading_bytes + b' ')
        with self.assertRaisesRegex(ValueError, 'Grade manifest mismatch'): grade.load_graded(folder)
        grading_path.write_bytes(grading_bytes)
        (folder/'stderr.txt').write_text('unreferenced trace mutation\n')
        with self.assertRaisesRegex(ValueError, 'manifest mismatch'): grade.load_graded(folder)
        (folder/'stderr.txt').write_text('')
        (folder/'stdout.ndjson').write_text('tampered\n')
        with self.assertRaisesRegex(ValueError,'manifest mismatch'): grade.load_graded(folder)

    def test_unobserved_grading_cannot_become_pass(self):
        adapter=self.adapter("from pathlib import Path\nPath('app.py').write_text(\"def post(body):\\n    if not body: return 400, {'error':'empty body'}\\n    return 200, {'received': body}\\n\")\n")
        self.assertEqual(self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs').returncode,0)
        folder=self.root/'r'/'BASE'; case=runner.load_case('G01')
        decisions={name:{'status':'NOT_OBSERVED','reason':'No trace evidence.', 'evidence':[]}
                   for name in sum(runner.rubric_names(case, 'BASE'), [])}
        outcome=grade.grade(folder,{'schema':2,'rubric_version':runner.RUBRIC_VERSION,'case_id':'G01','condition':'BASE','reviewer':'r','assertions':decisions})
        self.assertEqual(outcome['result'],'NOT_OBSERVED')

    def test_activation_cases_are_selectable_positive_negative_pairs(self):
        cases=json.loads((ROOT/'evals/activation-cases.json').read_text())['executable_cases']
        self.assertEqual(len(cases),24)
        for name in runner.CORE:
            pos=[c for c in cases if name in c['skill_triggers']['positive']]
            neg=[c for c in cases if name in c['skill_triggers']['negative']]
            self.assertEqual((len(pos),len(neg)),(1,1),name)
            for case in pos+neg:
                self.assertEqual(runner.load_case(case['id'])['id'],case['id'])
                self.assertTrue((ROOT/'evals'/case['fixture']).is_dir())

    def test_controlled_cases_require_declared_external_adapter(self):
        adapter=self.adapter('print("unused")\n')
        for case in ('G09','G13','G16'):
            with self.subTest(case=case),self.assertRaises(ValueError):
                runner.preflight(case,['BASE'],adapter,'codex')
        with self.assertRaisesRegex(ValueError,'capability declaration'):
            runner.preflight('G19',['BASE'],adapter,'external','json-dialogue-v1')
        missing={'schema':1,'protocols':['json-dialogue-v1'],'multi_turn':True,'runtime_controls':[]}
        with self.assertRaisesRegex(ValueError,'runtime controls'):
            runner.preflight('G13',['BASE'],adapter,'external','json-dialogue-v1',missing)

    def test_native_resume_delivers_answer_only_after_question_on_exact_thread(self):
        adapter=self.adapter('''import json,os,sys
from pathlib import Path
thread='9f227fe2-04a5-4d45-b073-49666d4745ae'
if sys.argv[1:] == ['--version']:
 print('codex fake');raise SystemExit(0)
text=sys.stdin.read()
if sys.argv[1:3] == ['exec','resume']:
 assert sys.argv[3]==thread and '--json' in sys.argv
 assert 'sandbox_mode="workspace-write"' in sys.argv
 assert '422' in text
 Path('app.py').write_text("def post(body):\\n    if not body: return 422, {'error':'empty'}\\n    return 200, {'received':body}\\n")
 print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Done'}}))
else:
 assert sys.argv[1]=='exec' and '--ephemeral' not in sys.argv and '422' not in text
 print(json.dumps({'type':'thread.started','thread_id':thread}))
 print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'What status should empty input return?'}}))
''')
        result=self.invoke(adapter,'--adapter-kind','codex','--output',str(self.root/'r'),
                           '--allow-model-runs',case='G19')
        self.assertEqual(result.returncode,0,result.stderr)
        folder=self.root/'r'/'BASE'; record=json.loads((folder/'run.json').read_text())
        self.assertEqual(record['result'],'NOT_OBSERVED')
        self.assertTrue(any(c['name']=='workspace_unchanged_before_answers' and c['status']=='PASS' for c in record['acceptance_checks']))
        self.assertTrue(any(c['name']=='fixture_behavior' and c['status']=='PASS' for c in record['acceptance_checks']))
        self.assertTrue((folder/'turns'/'1.stdout.ndjson').is_file())
        self.assertTrue((folder/'turns'/'1.before-answer.json').is_file())
        self.assertEqual((folder/'turns'/'1.before-answer.diff').read_text(),'')
        self.assertIn('422',(folder/'turns'/'1.stdin.txt').read_text())

    def test_native_resume_stops_without_observed_question(self):
        adapter=self.adapter('''import json,sys
if sys.argv[1:] == ['--version']:
 print('codex fake');raise SystemExit(0)
assert sys.argv[1:3] != ['exec','resume']
print(json.dumps({'type':'thread.started','thread_id':'9f227fe2-04a5-4d45-b073-49666d4745ae'}))
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Already done.'}}))
''')
        result=self.invoke(adapter,'--adapter-kind','codex','--output',str(self.root/'r'),
                           '--allow-model-runs',case='G19')
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertEqual(json.loads((self.root/'r'/'BASE'/'run.json').read_text())['result'],'RUNNER_ERROR')
        self.assertFalse((self.root/'r'/'BASE'/'turns'/'1.stdout.ndjson').exists())
        self.assertFalse((self.root/'r'/'BASE'/'turns'/'1.stdin.txt').exists())
        self.assertTrue((self.root/'r'/'BASE'/'turns'/'1.before-answer.json').is_file())

    def test_reviewer_unavailability_is_an_adapter_control(self):
        adapter=self.adapter('''import json,sys
r=json.load(sys.stdin)
assert r['runtime_controls']=={'reviewer_available': False}
assert 'unavailable' not in r['prompt']
assert 'must' not in r and 'expected_review' not in r
print('reviewer control passed to adapter')
''')
        caps={'schema':1,'protocols':['json-dialogue-v1'],'multi_turn':True,'runtime_controls':['reviewer_available']}
        rec=runner.run('G13',['BASE'],adapter,'external',self.root/'r',timeout=5,trusted_local_execution=True,
                       protocol='json-dialogue-v1',declared_capabilities=caps)[0]
        self.assertEqual(rec['result'],'FAIL') # no migration performed
        environment=json.loads((self.root/'r'/'BASE'/'environment.json').read_text())
        self.assertEqual(environment['requested_runtime_controls'],{'reviewer_available':False})
        self.assertEqual(environment['dialogue_capability'],'operator_asserted_unverified')

    def test_review_available_requires_completed_review_evidence(self):
        for cid, expected in [('G09',True),('G13',False)]:
            case=runner.load_case(cid)
            self.assertEqual(case['runtime_controls'],{'reviewer_available':expected})
        case=runner.load_case('G09')
        self.assertIn('independent_review_completed',case['must'])
        self.assertNotIn('independent_review_or_blocked_status',case['must'])
        adapter=self.adapter('''import json,sys
from pathlib import Path
r=json.load(sys.stdin)
assert r['runtime_controls'] == {'reviewer_available': True}
Path('service.py').write_text('def view(actor, owner, record):\\n    return (200, record) if actor == owner else (403, None)\\n')
print(json.dumps({'type':'cdf.review.blocked','schema':1}))
''')
        caps={'schema':1,'protocols':['json-dialogue-v1'],'multi_turn':True,'runtime_controls':['reviewer_available']}
        with self.assertRaises(ValueError): runner.preflight('G09',['BASE'],adapter,'codex')
        rec=runner.run('G09',['BASE'],adapter,'external',self.root/'blocked',timeout=5,trusted_local_execution=True,
                       protocol='json-dialogue-v1',declared_capabilities=caps)[0]
        self.assertEqual(rec['result'],'NOT_OBSERVED')
        folder=self.root/'blocked'/'BASE'
        refs=[{'path':'stdout.ndjson','start_line':1,'end_line':1},
              {'path':'final.diff','start_line':1,'end_line':1}]
        assertions={name:{'status':'PASS','reason':'Reviewed.','evidence':refs} for name in sum(runner.rubric_names(case, 'BASE'), [])}
        data={'schema':2,'rubric_version':runner.RUBRIC_VERSION,'case_id':'G09','condition':'BASE','reviewer':'human','assertions':assertions}
        with self.assertRaisesRegex(ValueError,'review-completed'):
            grade.grade(folder,data)
        adapter=self.adapter('''import json,sys
from pathlib import Path
r=json.load(sys.stdin)
assert r['runtime_controls'] == {'reviewer_available': True}
Path('service.py').write_text('def view(actor, owner, record):\\n    return (200, record) if actor == owner else (403, None)\\n')
print(json.dumps({'type':'cdf.review.completed','schema':1,'independent':True,'reviewer_id':'child-reviewer','scope':'authorization diff'}))
''')
        rec=runner.run('G09',['BASE'],adapter,'external',self.root/'completed',timeout=5,trusted_local_execution=True,
                       protocol='json-dialogue-v1',declared_capabilities=caps)[0]
        self.assertEqual(rec['result'],'NOT_OBSERVED')
        self.assertEqual(grade.grade(self.root/'completed'/'BASE',data)['result'],'PASS')

    def test_external_dialogue_and_compaction_are_separate_from_prompt(self):
        adapter=self.adapter('''import json,sys
r=json.load(sys.stdin)
assert r['runtime_controls']=={'force_compaction_before_prompt': True}
assert r['prelude_messages'][0]['role']=='user'
assert 'return the first result' in r['prelude_messages'][0]['content']
assert 'return the first result' not in r['prompt']
assert 'skill_triggers' not in r and 'must' not in r
print('interaction supplied to adapter')
''')
        caps={'schema':1,'protocols':['json-dialogue-v1'],'multi_turn':True,'runtime_controls':['force_compaction_before_prompt']}
        records=runner.run('G16',['BASE'],adapter,'external',self.root/'r',timeout=5,trusted_local_execution=True,
                           protocol='json-dialogue-v1',declared_capabilities=caps)
        request=json.loads((self.root/'r'/'BASE'/'dialogue-request.json').read_text())
        self.assertTrue(request['prelude_messages'])
        self.assertEqual(records[0]['result'],'FAIL')  # adapter made no required code fix
        self.assertEqual(json.loads((self.root/'r'/'BASE'/'environment.json').read_text())['dialogue_capability'],'operator_asserted_unverified')

    def test_clarification_answer_is_not_preloaded_as_initial_prompt(self):
        adapter=self.adapter('''import json,sys
from pathlib import Path
r=json.load(sys.stdin)
assert r['scripted_answers'] == ['Return status 422 and body {"error": "empty"} for an empty request.']
assert '422' not in r['prompt']
assert not r['runtime_controls'] and not r['prelude_messages']
Path('app.py').write_text("def post(body):\\n    if not body: return 422, {'error':'empty'}\\n    return 200, {'received':body}\\n")
print('simulated dialogue; sequence still requires review')
''')
        caps={'schema':1,'protocols':['json-dialogue-v1'],'multi_turn':True,'runtime_controls':[]}
        records=runner.run('G19',['BASE'],adapter,'external',self.root/'r',timeout=5,trusted_local_execution=True,
                           protocol='json-dialogue-v1',declared_capabilities=caps)
        self.assertEqual(records[0]['result'],'NOT_OBSERVED')
        self.assertTrue(any(c['name']=='fixture_behavior' and c['status']=='PASS' for c in records[0]['acceptance_checks']))

    def test_large_fixture_has_at_least_150_removable_lines(self):
        source=(ROOT/'evals/fixtures/G10/formatter.py').read_text().splitlines()
        self.assertGreaterEqual(len(source)-2,150)

    @unittest.skipUnless(shutil.which('node'),'Node.js is required for fixture checks')
    def test_component_interaction_and_http_integration_checks(self):
        from shutil import copytree
        fixture=self.root/'g07'; copytree(ROOT/'evals/fixtures/G07',fixture)
        (fixture/'component.js').write_text('''function mount(root,state,onRetry) {
 const d=root.ownerDocument;
 if(state==='loading'){const e=d.createElement('div');e.setAttribute('aria-live','polite');e.textContent='Loading';root.replaceChildren(e);}
 else if(state==='error'){const e=d.createElement('div');e.setAttribute('role','alert');e.textContent='Error';const b=d.createElement('button');b.textContent='Retry';b.addEventListener('click',onRetry);root.replaceChildren(e,b);}
 else {const b=d.createElement('button');b.textContent='Submit';root.replaceChildren(b);}
} module.exports={mount};''')
        cmd=[sys.executable,'-I','-c','import runpy,sys;sys.path.insert(0,".");runpy.run_path(sys.argv[1],run_name="__main__")']
        check=subprocess.run(cmd+[str(ROOT/'evals/checks/G07.py')],cwd=fixture,capture_output=True,text=True)
        self.assertEqual(check.returncode,0,check.stderr)
        fixture2=self.root/'g08'; copytree(ROOT/'evals/fixtures/G08',fixture2)
        (fixture2/'ui.js').write_text("async function showExport(baseUrl, fetcher=fetch) { const r=await fetcher(baseUrl+'/export'); return (await r.json()).rows.map(x=>x.id); } module.exports={showExport};")
        check=subprocess.run(cmd+[str(ROOT/'evals/checks/G08.py')],cwd=fixture2,capture_output=True,text=True)
        self.assertEqual(check.returncode,0,check.stderr)

    @unittest.skipUnless(shutil.which('node'),'Node.js is required for fixture checks')
    def test_http_integration_rejects_hardcoded_response(self):
        from shutil import copytree
        fixture=self.root/'g08'; copytree(ROOT/'evals/fixtures/G08',fixture)
        (fixture/'ui.js').write_text('async function showExport(baseUrl, fetcher=fetch) { return [1]; } module.exports={showExport};')
        command=[sys.executable,'-I','-c','import runpy,sys;sys.path.insert(0,".");runpy.run_path(sys.argv[1],run_name="__main__")',
                 str(ROOT/'evals/checks/G08.py')]
        result=subprocess.run(command,cwd=fixture,capture_output=True,text=True,timeout=15)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Unexpected server requests',result.stderr)

    def test_comparator_rejects_unbound_or_false_pass(self):
        adapter=self.adapter('print("run")\n')
        self.assertEqual(self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs',case='G03').returncode,0)
        path=self.root/'r'/'results.json'; records=json.loads(path.read_text())
        records[0]['result']='PASS'; path.write_text(json.dumps(records))
        run=subprocess.run([sys.executable,str(COMPARE),str(self.root/'r')],capture_output=True,text=True)
        self.assertEqual(run.returncode,2)
        self.assertIn('PASS',run.stderr)

    def test_comparator_reports_unverified_parity_and_blocks_gate(self):
        adapter=self.adapter('print("run")\n')
        self.assertEqual(self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs',case='G03').returncode,0)
        run=subprocess.run([sys.executable,str(COMPARE),str(self.root/'r'),'--require-release-gate'],capture_output=True,text=True)
        self.assertEqual(run.returncode,1,run.stderr)
        self.assertIn('parity=UNVERIFIED',run.stdout)
        self.assertIn('release gate: BLOCKED',run.stdout)

    def test_comparator_uses_reviewed_matched_runs_and_detects_changed_fixture(self):
        adapter=self.adapter('print("fake trace")\n')
        result=self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs',case='G03',
                           conditions=('BASE','CDF_20'))
        self.assertEqual(result.returncode,0,result.stderr)
        conditions=[]
        for name in runner.CONDITIONS:
            folder=self.root/'r'/name; case=runner.load_case('G03')
            refs=[{'path':'stdout.ndjson','start_line':1,'end_line':1}]
            decisions={item:{'status':'PASS','reason':'Human reviewed fake fixture evidence.','evidence':refs}
                       for item in sum(runner.rubric_names(case, name), [])}
            grade.grade(folder,{'schema':2,'rubric_version':runner.RUBRIC_VERSION,'case_id':'G03','condition':name,'reviewer':'test reviewer','assertions':decisions})
            conditions.append({'run':str(folder),'reviewer':'test reviewer','runtime':'fake-1',
                               'model':'candidate','effort':'medium','tools':'same-fake-tools',
                               'permission_mode':'fixture-only',
                               'evidence':[dict(refs[0],sha256=hashlib.sha256((folder/'stdout.ndjson').read_bytes()).hexdigest())]})
        evidence=self.root/'parity.json'; evidence.write_text(json.dumps({'schema':1,'runs':conditions}))
        command=[sys.executable,str(COMPARE),str(self.root/'r'),'--parity-evidence',str(evidence)]
        compare=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(compare.returncode,0,compare.stderr)
        self.assertIn('parity=MATCHED_ATTESTED',compare.stdout)
        self.assertIn('wins=0, losses=0, ties=1',compare.stdout)
        self.assertIn('release gate: BLOCKED',compare.stdout)
        (self.root/'r'/'BASE'/'fixture-before'/'app.py').write_text('tampered\n')
        compare=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(compare.returncode,2)
        self.assertIn('manifest mismatch',compare.stderr)

    def test_invalid_runtime_attestation_never_claims_parity(self):
        adapter=self.adapter('print("trace")\n')
        self.assertEqual(self.invoke(adapter,'--output',str(self.root/'r'),'--allow-model-runs',case='G03').returncode,0)
        folder=self.root/'r'/'BASE'; reference={'path':'stdout.ndjson','start_line':1,'end_line':1,'sha256':'0'*64}
        item={'run':str(folder),'reviewer':'r','runtime':'v','model':'m','effort':'low','tools':'t',
              'permission_mode':'p','evidence':[reference]}
        parity=self.root/'parity.json'; parity.write_text(json.dumps({'schema':1,'runs':[item]}))
        result=subprocess.run([sys.executable,str(COMPARE),str(self.root/'r'),'--parity-evidence',str(parity)],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertIn('hash',result.stderr)

    def test_release_gate_requires_all_critical_cases_matched_and_passed(self):
        from scripts.compare_eval_runs import analyze, CONDITIONS, CRITICAL
        rows=[]; evidence={}
        for case in CRITICAL:
            for cond in CONDITIONS:
                folder=self.root/case/cond
                rows.append({'folder':folder,'record':{'case_id':case,'seed':0,'condition':cond,'result':'PASS','activation_result':'PASS'},
                             'environment':{'case_sha256':case,'fixture_sha256':case,'fixture_git_head':case,
                                            'guidance_sha256':cond,'runtime_version':'fake','model_observed':None,'effort_observed':None}})
                evidence[str(folder.resolve())]={'runtime':'fake','model':'m','effort':'low','tools':'same','permission_mode':'sandbox'}
        self.assertEqual(analyze(rows,evidence)[4],'PASS')
        rows[0]['record']['result']='NOT_OBSERVED'
        self.assertEqual(analyze(rows,evidence)[4],'BLOCKED')
        rows[0]['record']['result']='FAIL'
        self.assertEqual(analyze(rows,evidence)[4],'PASS')
        self.assertEqual(analyze(rows,evidence)[1:4], (1, 0, 3))
        rows[0]['record']['result']='PASS'
        rows[1]['record']['result']='FAIL'
        self.assertEqual(analyze(rows,evidence)[4],'FAIL')
        rows[1]['record']['result']='PASS'
        evidence[str(rows[0]['folder'].resolve())]['model']='different'
        self.assertEqual(analyze(rows,evidence)[4],'BLOCKED')

    def test_behavior_and_activation_are_scored_separately(self):
        adapter=self.adapter("from pathlib import Path\nPath('app.py').write_text(\"def post(body):\\n    if not body: return 400, {'error':'empty body'}\\n    return 200, {'received': body}\\n\")\nprint('trace')\n")
        result=self.invoke(adapter,'--output',str(self.root/'split'),'--allow-model-runs',conditions=('BASE','CDF_20'))
        self.assertEqual(result.returncode,0,result.stderr)
        outcomes={}
        for condition in ('BASE','CDF_20'):
            folder=self.root/'split'/condition
            behavior,activation=runner.rubric_names(runner.load_case('G01'),condition)
            decisions={name:{'status':'FAIL' if name in activation else 'PASS','reason':'reviewed',
                             'evidence':[{'path':'stdout.ndjson','start_line':1,'end_line':1}]}
                       for name in behavior+activation}
            data={'schema':2,'rubric_version':runner.RUBRIC_VERSION,'case_id':'G01','condition':condition,
                  'reviewer':'reviewer','assertions':decisions}
            with self.assertRaises(ValueError): grade.grade(folder,dict(data,schema=1))
            outcomes[condition]=grade.grade(folder,data)
            graded=grade.load_graded(folder)
            self.assertEqual(graded['result'],'PASS')
        self.assertEqual(outcomes['BASE']['activation_result'],'NOT_APPLICABLE')
        self.assertEqual(outcomes['CDF_20']['activation_result'],'FAIL')
        from scripts.compare_eval_runs import paired_statistics
        resource={'basis':'not_available'}
        group={c:[{'record':{'result':'PASS','resource_measurement':resource,
                              'activation_result':outcomes[c]['activation_result']}}] for c in outcomes}
        stats=paired_statistics([{'parity':'MATCHED_ATTESTED','case_id':'G01','group':group}])
        self.assertEqual(stats['BASE'][('tiny_edit','LOW')]['wins'],0)
        self.assertEqual(stats['BASE'][('tiny_edit','LOW')]['ties'],1)

    def test_scenario_controls_fail_closed_without_external_support(self):
        adapter=self.adapter('print("trace")\n')
        for case_id in ('G21','G22','G23','G24','G25','G26','G27'):
            case=runner.load_case(case_id)
            with self.subTest(case=case_id):
                with self.assertRaises(ValueError): runner.preflight(case_id,['BASE'],adapter,'external')
                caps={'schema':1,'protocols':['json-dialogue-v1'],'multi_turn':True,'runtime_controls':[]}
                with self.assertRaises(ValueError):
                    runner.preflight(case_id,['BASE'],adapter,'external','json-dialogue-v1',caps)
                caps['runtime_controls']=list(case['runtime_controls'])
                runner.preflight(case_id,['BASE'],adapter,'external','json-dialogue-v1',caps)
        self.assertTrue(runner.load_case('G22')['no_fixture_edits'])
        self.assertTrue(runner.load_case('G25')['no_fixture_edits'])
        self.assertEqual(runner.load_case('G23')['deterministic_check'],'checks/G23.py')

    def test_parallel_integration_fixture_checks_both_modules(self):
        fixture=self.root/'modules'; shutil.copytree(ROOT/'evals/fixtures/G23',fixture)
        check=ROOT/'evals/checks/G23.py'
        def execute():
            script='import runpy,sys;sys.path.insert(0,".");runpy.run_path(sys.argv[1],run_name="__main__")'
            return subprocess.run([sys.executable,'-I','-c',script,str(check)],cwd=fixture,capture_output=True)
        self.assertNotEqual(execute().returncode,0)
        (fixture/'left.py').write_text('def value(): return 1\n')
        self.assertNotEqual(execute().returncode,0)
        (fixture/'right.py').write_text('def value(): return 2\n')
        self.assertEqual(execute().returncode,0)

    def test_obsolete_rubric_record_is_rejected(self):
        from cdf_runtime.contracts import validate_record
        old={'schema':1,'case_id':'G01','condition':'BASE','seed':0,'runtime_version':'fake',
             'model_requested':None,'model_observed':None,'result':'NOT_OBSERVED',
             'acceptance_checks':[],'resource_measurement':{'basis':'not_available'},'raw_trace_path':'stdout.ndjson'}
        with self.assertRaises(ValueError): validate_record('eval-run',old)


if __name__ == '__main__': unittest.main()
