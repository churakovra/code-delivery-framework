#!/usr/bin/env python3
"""Compare evidence-bound CDF runs; unknown results never satisfy release gates."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cdf_runtime.contracts import validate_record
from evals.grade import _evidence, load_graded
from evals.conditions import ALL_CONDITIONS, CANDIDATE_CONDITIONS, validate_guidance_identity
from evals.runner import activation_rubric_hash, _case_hash, _hash_snapshot, _snapshot, _usage, load_case, rubric_names
from evals.evidence import verify_manifest

CONDITIONS = ('BASE', 'CDF_20')
CRITICAL = ('G01', 'G02', 'G09', 'G13')
CANDIDATE_CRITICAL = ('G01', 'G02', 'G05', 'G07', 'G08', 'G09', 'G13', 'G14',
                      'G19', 'G28', 'G29', 'G30', 'G31', 'E03', 'E07', 'E09',
                      'E10', 'E12', 'E16')


def comparison_conditions(group):
    return CANDIDATE_CONDITIONS if set(group) & {'LEGACY_CDF_11', 'CANDIDATE_CDF'} else CONDITIONS


def candidate_condition(group):
    return 'CANDIDATE_CDF' if comparison_conditions(group) == CANDIDATE_CONDITIONS else 'CDF_20'



def read_run(folder, record):
    if record.get('condition') not in ALL_CONDITIONS: raise ValueError('Unknown result condition')
    condition = folder / record['condition']
    verify_manifest(condition)
    original = json.loads((condition / 'run.json').read_text())
    validate_record('eval-run', original)
    validate_record('eval-run', record)
    if record != original: raise ValueError('Summary does not match condition run.json')
    if original['result'] == 'PASS': raise ValueError('Ungraded run cannot be PASS')
    if original['raw_trace_path'] != 'stdout.ndjson' or not (condition/'stdout.ndjson').is_file():
        raise ValueError('Run trace is missing or has an unsafe path')
    environment_path = condition/'environment.json'
    environment = json.loads(environment_path.read_text()) if environment_path.is_file() else {}
    if original['result'] != 'RUNNER_ERROR': validate_guidance_identity(condition, original['condition'], environment)
    if original['result'] != 'RUNNER_ERROR' and original['resource_measurement']['elapsed_seconds'] != json.loads((condition / 'timing.json').read_text())['elapsed_seconds']:
        raise ValueError('Resource elapsed time disagrees with timing evidence')
    if original['resource_measurement'] != _usage((condition / 'stdout.ndjson').read_bytes(), environment.get('adapter_kind'), original['resource_measurement']['elapsed_seconds']):
        raise ValueError('Resource measurement disagrees with trace')
    if original['result'] != 'RUNNER_ERROR':
        command = json.loads((condition / 'command.json').read_text())
        timeout = command.get('timeout_seconds')
        if type(timeout) is not int or timeout < 1:
            raise ValueError('Command evidence lacks a valid timeout')
        if 'timeout_seconds' in environment and (type(environment['timeout_seconds']) is not int or environment['timeout_seconds'] != timeout):
            raise ValueError('Environment timeout disagrees with command evidence')
        # Archived records remain readable; derive their timeout from immutable
        # command evidence rather than guessing an absent environment field.
        environment = dict(environment, timeout_seconds=timeout)
        case = load_case(original['case_id'])
        if environment.get('case_sha256') != _case_hash(case): raise ValueError('Case identity differs from recorded run')
        if original['condition'] == 'CANDIDATE_CDF' and environment.get('activation_rubric_sha256') != activation_rubric_hash(case, original['condition']):
            raise ValueError('Candidate activation rubric changed since the run')
        behavior, activation = rubric_names(case, original['condition'])
        if [c['name'] for c in original['activation_checks']] != activation or any(c['status'] != 'NOT_OBSERVED' for c in original['activation_checks']):
            raise ValueError('Original activation checks do not match rubric')
        if [c['name'] for c in original['acceptance_checks'] if c['name'] in behavior] != behavior:
            raise ValueError('Original behavior checks do not match rubric')
        if json.loads((condition/'project-checks.json').read_text()) != original['acceptance_checks']:
            raise ValueError('Check artifact differs from condition run.json')
        if (condition/'initial_sha.txt').read_text().strip() != environment.get('fixture_git_head'):
            raise ValueError('Initial fixture Git identity differs from environment')
        fixture = condition/'fixture-before'
        if _hash_snapshot(_snapshot(fixture, skip_git=True)) != environment.get('fixture_sha256'):
            raise ValueError('Initial fixture differs from recorded hash')
    grade_files = [condition/name for name in ('grading.json', 'graded-run.json', 'grade-manifest.json')]
    if any(path.exists() for path in grade_files) and not all(path.is_file() for path in grade_files):
        raise ValueError('Incomplete grading evidence')
    reviewed = load_graded(condition) if all(path.is_file() for path in grade_files) else original
    validate_record('eval-run', reviewed)
    return {'record': reviewed, 'environment': environment, 'folder': condition}


def attestations(path, entries):
    if path is None: return {}
    data = json.loads(path.read_text())
    if data.get('schema') != 1 or not isinstance(data.get('runs'), list): raise ValueError('Invalid parity evidence')
    allowed = {str(e['folder'].resolve()):e for e in entries}
    result = {}
    for item in data['runs']:
        key = str(Path(item['run']).resolve())
        if key not in allowed or key in result: raise ValueError('Unknown or duplicate parity run')
        if not isinstance(item.get('reviewer'), str) or not item['reviewer'].strip(): raise ValueError('Parity reviewer required')
        for field in ('runtime', 'model', 'effort', 'tools', 'permission_mode'):
            if not isinstance(item.get(field), str) or not item[field].strip() or item[field] == 'unverified':
                raise ValueError('Parity evidence requires observed runtime, model, effort, tools and permission mode')
        for field in ('network_policy', 'credentials_policy'):
            if field in item and (not isinstance(item[field], str) or not item[field].strip() or item[field] == 'unverified'):
                raise ValueError('Policy attestation must be a nonempty observed policy description')
        # Existence and hashes are checked; a person is responsible for interpreting the trace.
        supplied_refs = item.get('evidence')
        if not isinstance(supplied_refs, list) or not supplied_refs:
            raise ValueError('Parity evidence references required')
        refs = _evidence(allowed[key]['folder'], [{k: ref[k] for k in ('path','start_line','end_line')}
                                                  for ref in supplied_refs])
        if any(ref.get('sha256') != actual['sha256'] for ref, actual in zip(supplied_refs, refs)):
            raise ValueError('Parity evidence hash does not match the cited artifact')
        result[key] = {'runtime':item['runtime'],'model':item['model'],'effort':item['effort'],
                       'tools':item['tools'],'permission_mode':item['permission_mode'],
                       'reviewer':item['reviewer'],'evidence_refs':refs,
                       'network_policy':item.get('network_policy'),
                       'credentials_policy':item.get('credentials_policy')}
    return result


def group_parity(group, evidence, regime='standardized'):
    required = comparison_conditions(group)
    if set(group) != set(required) or any(len(rows)!=1 for rows in group.values()):
        return 'UNVERIFIED', 'missing or duplicate conditions'
    rows = [group[c][0] for c in required]
    timeouts = [row['environment'].get('timeout_seconds') for row in rows]
    if required == CANDIDATE_CONDITIONS or any(value is not None for value in timeouts):
        if any(type(value) is not int or value < 1 for value in timeouts):
            return 'UNVERIFIED', 'effective timeout unavailable'
        if len(set(timeouts)) != 1:
            return 'MISMATCH', 'timeout_seconds differs'
    for field in ('case_sha256','fixture_sha256','fixture_git_head'):
        values = [r['environment'].get(field) for r in rows]
        if any(v is None for v in values): return 'UNVERIFIED', f'{field} unavailable'
        if len(set(values)) != 1: return 'MISMATCH', f'{field} differs'
    for field in ('adapter_kind','adapter_protocol','model_requested','effort_requested','requested_runtime_controls'):
        values = [json.dumps(r['environment'].get(field), sort_keys=True) for r in rows]
        if len(set(values)) != 1: return 'MISMATCH', f'{field} differs'
    for row in rows:
        if not row['environment'].get('guidance_sha256'): return 'UNVERIFIED', 'guidance hash unavailable'
    attested = [evidence.get(str(r['folder'].resolve())) for r in rows]
    if any(a is None for a in attested): return 'UNVERIFIED', 'runtime parity evidence absent'
    if required == CANDIDATE_CONDITIONS:
        for field in ('network_policy', 'credentials_policy'):
            values = [item.get(field) for item in attested]
            if any(not isinstance(value, str) or not value.strip() or value == 'unverified' for value in values):
                return 'UNVERIFIED', f'{field} attestation unavailable'
            if len(set(values)) != 1:
                return 'MISMATCH', f'{field} differs'
    for field in (('runtime','model','effort','tools','permission_mode') if regime == 'standardized' else ('runtime','model','effort','permission_mode')):
        if len({a[field] for a in attested}) != 1: return 'MISMATCH', f'{field} differs'
    for row, a in zip(rows, attested):
        env = row['environment']
        for recorded, attested_key in [('runtime_version','runtime'),('model_observed','model'),('effort_observed','effort')]:
            value=env.get(recorded)
            if value not in (None,'unverified') and value != a[attested_key]: return 'MISMATCH', f'{recorded} disagrees with evidence'
    return 'MATCHED_ATTESTED', 'reviewer-attested; interpretation remains human judgment'


def analyze(entries, evidence, regime='standardized'):
    groups=defaultdict(lambda: defaultdict(list))
    for entry in entries:
        r=entry['record']; groups[(r['case_id'],r['seed'])][r['condition']].append(entry)
    guidance=defaultdict(set)
    for row in entries:
        digest=row['environment'].get('guidance_sha256')
        if digest: guidance[row['record']['condition']].add(digest)
    # Framework guidance hashes must remain consistent across repeated runs.
    changing={k for k,v in guidance.items() if len(v)>1 and k in ('CDF_20', 'LEGACY_CDF_11', 'CANDIDATE_CDF')}
    is_candidate = any(row['record']['condition'] in ('CANDIDATE_CDF', 'LEGACY_CDF_11') for row in entries)
    summaries=[]; wins=losses=ties=0
    for key,group in sorted(groups.items()):
        parity,why=group_parity(group,evidence,regime)
        if is_candidate and set(group) != set(CANDIDATE_CONDITIONS):
            parity,why='UNVERIFIED','historical pairs cannot substitute for candidate three-way comparisons'
        if changing and parity=='MATCHED_ATTESTED': parity,why='MISMATCH','guidance hash changed within a condition'
        if parity=='MATCHED_ATTESTED':
            base=group['BASE'][0]['record']['result']; new=group[candidate_condition(group)][0]['record']['result']
            if base in ('PASS','FAIL') and new in ('PASS','FAIL'):
                wins += new=='PASS' and base=='FAIL'; losses += new=='FAIL' and base=='PASS'; ties += new==base
        summaries.append({'case_id':key[0],'seed':key[1],'parity':parity,'reason':why,'group':group})
    needed = set(CANDIDATE_CRITICAL if is_candidate else CRITICAL)
    bycase=defaultdict(list)
    for summary in summaries: bycase[summary['case_id']].append(summary)
    selected=[summary for case in needed for summary in bycase.get(case, [])]
    failed = False
    blocked = any(case not in bycase for case in needed)
    for summary in summaries:
        group = summary['group']; candidate = candidate_condition(group)
        candidate_rows = group.get(candidate, [])
        case = load_case(summary['case_id'])
        safety = case.get('critical_safety', False)
        for row in candidate_rows:
            record = row['record']
            if ((summary['case_id'] in needed or safety) and record['result'] == 'FAIL'):
                failed = True
            if any(check.get('status') == 'FAIL' and check.get('name') in
                   ('git_policy_metadata_unchanged', 'git_head_branch_and_index_unchanged', 'fixture_source_unchanged')
                   for check in record.get('acceptance_checks', [])):
                failed = True
            # Historical process gate is preserved. Candidate activation remains
            # diagnostic and never substitutes for observed outcome assertions.
            if not is_candidate and summary['case_id'] in needed and record.get('activation_result') == 'FAIL':
                failed = True
        if summary['case_id'] not in needed: continue
        if summary['parity'] != 'MATCHED_ATTESTED':
            blocked = True; continue
        record = group[candidate][0]['record']
        if record['result'] != 'PASS': blocked = True
        if not is_candidate and record.get('activation_result') not in ('PASS', 'NOT_APPLICABLE'):
            blocked = True
        if any(group[name][0]['record']['result'] not in ('PASS', 'FAIL') for name in comparison_conditions(group) if name != candidate):
            blocked = True
    gate = 'FAIL' if failed else 'BLOCKED' if blocked else 'PASS'
    # Installed integration setup is not independently observed by this runner.
    if regime == 'installed-system' and gate == 'PASS': gate = 'BLOCKED'
    return summaries, wins, losses, ties, gate


def paired_statistics(summaries):
    results = {name: defaultdict(lambda: {'wins':0,'losses':0,'ties':0,'candidate_tokens':0,
                                         'baseline_tokens':0,'candidate_passes':0,'baseline_passes':0,
                                         'measured_pairs':0}) for name in (('BASE', 'LEGACY_CDF_11') if any('CANDIDATE_CDF' in summary['group'] for summary in summaries) else ('BASE',))}
    for summary in summaries:
        if summary['parity'] != 'MATCHED_ATTESTED': continue
        case=load_case(summary['case_id']); key=(case['class'],case['risk'])
        new=summary['group'][candidate_condition(summary['group'])][0]['record']
        for baseline in results:
            if baseline not in summary['group']: continue
            old=summary['group'][baseline][0]['record']
            if new['result'] not in ('PASS','FAIL') or old['result'] not in ('PASS','FAIL'): continue
            r=results[baseline][key]
            r['wins'] += new['result']=='PASS' and old['result']=='FAIL'
            r['losses'] += new['result']=='FAIL' and old['result']=='PASS'
            r['ties'] += new['result']==old['result']
            n=new['resource_measurement']; b=old['resource_measurement']
            if all(x.get('basis')=='observed_runtime' and type(x.get('input_tokens')) is int and
                   type(x.get('output_tokens')) is int and x['input_tokens']+x['output_tokens']>0 for x in (n,b)):
                r['measured_pairs']+=1
                r['candidate_tokens']+=n['input_tokens']+n['output_tokens']
                r['baseline_tokens']+=b['input_tokens']+b['output_tokens']
                r['candidate_passes']+=new['result']=='PASS'; r['baseline_passes']+=old['result']=='PASS'
    return results


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('runs',nargs='+',type=Path,help='Directories containing results.json')
    p.add_argument('--regime', choices=('standardized', 'installed-system'), default='standardized', help='Comparison regime; installed-system permits attested condition-specific tools')
    p.add_argument('--csv',type=Path,help='New CSV path; never overwrite')
    p.add_argument('--parity-evidence',type=Path,help='Reviewer-attested runtime parity evidence JSON')
    p.add_argument('--require-release-gate',action='store_true',help='Return nonzero unless the evaluation gate passes')
    args=p.parse_args()
    try:
        entries=[]
        for folder in args.runs:
            manifest=json.loads((folder/'manifest.json').read_text())
            records=json.loads((folder/'results.json').read_text())
            if {r['condition'] for r in records} != set(manifest['conditions']) or len(records)!=len(manifest['conditions']):
                raise ValueError('Results do not match manifest conditions')
            for record in records:
                if record['case_id']!=manifest['case_id'] or record['seed']!=manifest['seed']:
                    raise ValueError('Result identity does not match manifest')
                entries.append(read_run(folder,record))
        evidence=attestations(args.parity_evidence,entries)
        summaries,wins,losses,ties,gate=analyze(entries,evidence,args.regime)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(f'comparison error: {exc}',file=sys.stderr); return 2
    print(f'Comparison regime: {args.regime}; installed-system comparisons are descriptive and do not isolate guidance effects.' if args.regime == 'installed-system' else 'Comparison regime: standardized; equal attested tools required.')
    print('| Case | Condition | Behavior | Activation | Unobserved checks |')
    print('| --- | --- | --- | --- | ---: |')
    for item in entries:
        r=item['record']; n=sum(c['status'] in ('NOT_OBSERVED','SKIPPED') for c in r['acceptance_checks'])
        print(f'| {r["case_id"]} | {r["condition"]} | {r["result"]} | {r["activation_result"]} | {n} |')
    for row in summaries: print(f'{row["case_id"]} seed={row["seed"]} parity={row["parity"]}: {row["reason"]}')
    label = 'CANDIDATE_CDF' if any('CANDIDATE_CDF' in row['group'] for row in summaries) else 'CDF_20'
    for baseline,strata in paired_statistics(summaries).items():
        if not strata: print(f'{label} vs {baseline}: no comparable scored pairs; uncertainty not estimable.')
        for (case_class,risk),values in sorted(strata.items()):
            n=values['wins']+values['losses']+values['ties']
            uncertainty='insufficient paired data' if n<5 else 'descriptive only; uncertainty not quantified'
            print(f'{label} vs {baseline} class={case_class} risk={risk}: n={n}, wins={values["wins"]}, losses={values["losses"]}, ties={values["ties"]}; {uncertainty}.')
            if values['measured_pairs']:
                print(f'Observed trace resource: {label} {values["candidate_passes"]} passes / {values["candidate_tokens"]} tokens; {baseline} {values["baseline_passes"]} passes / {values["baseline_tokens"]} tokens, pairs={values["measured_pairs"]}. Not subscription allowance.')
            else: print('Resource-normalized outcomes unavailable: no matched observed token measurements.')
    print(f'Evaluation release gate: {gate}; this gate does not replace installer, security, or release review gates.')
    if args.csv:
        with args.csv.open('x',newline='') as f:
            writer=csv.writer(f); writer.writerow(['case_id','condition','result','activation_result','unobserved_checks'])
            for item in entries:
                r=item['record']; writer.writerow([r['case_id'],r['condition'],r['result'],r['activation_result'],sum(c['status'] in ('NOT_OBSERVED','SKIPPED') for c in r['acceptance_checks'])])
    return 1 if args.require_release_gate and gate!='PASS' else 0

if __name__ == '__main__': raise SystemExit(main())
