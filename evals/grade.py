"""Record a human-reviewed grading decision with pointers to actual run evidence.

This only records a reviewer's assessment. It checks that evidence references are
real and immutable by hash; it does not independently judge their interpretation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .runner import RUBRIC_VERSION, _case_hash, _json, _usage, load_case, rubric_names, scored_status
from .evidence import verify_manifest, write_grade_manifest, verify_grade_manifest
from cdf_runtime.contracts import validate_record


def _evidence(folder: Path, references):
    if not isinstance(references, list) or not references:
        raise ValueError('A pass or fail needs at least one evidence reference')
    manifest = json.loads((folder / 'evidence-manifest.json').read_text())
    result = []
    for ref in references:
        if not isinstance(ref, dict) or set(ref) != {'path', 'start_line', 'end_line'}:
            raise ValueError('Evidence requires path, start_line and end_line')
        if ref['path'] not in manifest['files']:
            raise ValueError('Evidence is not bound by the source manifest')
        relative = Path(ref['path'])
        if relative.is_absolute() or '..' in relative.parts or not relative.parts:
            raise ValueError('Unsafe evidence path')
        path = folder
        for part in relative.parts:
            path /= part
            if path.is_symlink(): raise ValueError('Symlink evidence is not accepted')
        if not path.is_file() or not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError('Evidence file is missing or outside the run')
        data = path.read_bytes()
        try: lines = data.decode('utf-8').splitlines()
        except UnicodeDecodeError as exc: raise ValueError('Evidence must be UTF-8 text') from exc
        first, last = ref['start_line'], ref['end_line']
        if type(first) is not int or type(last) is not int or first < 1 or last < first or last > len(lines):
            raise ValueError('Evidence line range does not exist')
        result.append(dict(ref, sha256=hashlib.sha256(data).hexdigest()))
    return result


def _has_completed_review_event(folder: Path, refs):
    """Require a cited independent-review event and a cited actual diff.

    This checks the adapter's recorded claim. A human must still verify the
    event and the review's independence and scope against the actual trace.
    """
    if not any(ref['path'] == 'final.diff' for ref in refs):
        return False
    for ref in refs:
        if ref['path'] != 'stdout.ndjson': continue
        lines = (folder / ref['path']).read_text().splitlines()
        for line in lines[ref['start_line'] - 1:ref['end_line']]:
            try: event = json.loads(line)
            except ValueError: continue
            if (isinstance(event, dict) and event.get('type') == 'cdf.review.completed'
                and event.get('schema') == 1 and event.get('independent') is True
                and isinstance(event.get('reviewer_id'), str) and event['reviewer_id'].strip()
                and event['reviewer_id'].strip().lower() not in ('root', 'master', 'main')
                and isinstance(event.get('scope'), str) and event['scope'].strip()):
                return True
    return False


def grade(folder: Path, supplied):
    folder = folder.resolve()
    manifest_hash = verify_manifest(folder)
    run_bytes = (folder / 'run.json').read_bytes()
    run = json.loads(run_bytes)
    case = load_case(run['case_id'])
    environment = json.loads((folder / 'environment.json').read_text())
    timing = json.loads((folder / 'timing.json').read_text())
    if run['resource_measurement']['elapsed_seconds'] != timing['elapsed_seconds']:
        raise ValueError('Resource elapsed time disagrees with timing evidence')
    if run['resource_measurement'] != _usage((folder / 'stdout.ndjson').read_bytes(), environment.get('adapter_kind'), run['resource_measurement']['elapsed_seconds']):
        raise ValueError('Resource measurement disagrees with trace')
    if environment.get('case_sha256') != _case_hash(case):
        raise ValueError('The case or grading rubric changed since the run')
    if run['condition'] not in ('BASE', 'CDF_06', 'CDF_20'):
        raise ValueError('Unknown condition')
    validate_record('eval-run', run)
    if supplied.get('schema') != 2 or supplied.get('rubric_version') != RUBRIC_VERSION or supplied.get('case_id') != run['case_id'] or supplied.get('condition') != run['condition']:
        raise ValueError('Annotation identity does not match the run')
    reviewer = supplied.get('reviewer')
    if not isinstance(reviewer, str) or not reviewer.strip(): raise ValueError('Reviewer identity is required')
    assertions = supplied.get('assertions')
    behavior_names, activation_names = rubric_names(case, run['condition'])
    names = behavior_names + activation_names
    if not isinstance(assertions, dict) or set(assertions) != set(names):
        raise ValueError('Provide a decision for every named assertion')
    graded = []
    for check in run['acceptance_checks'] + run['activation_checks']:
        if check['name'] not in assertions:
            graded.append(check)
            continue
        # A reviewer cannot overwrite a deterministic check or a previous grade.
        if check['status'] != 'NOT_OBSERVED': raise ValueError('Named assertion already graded')
        decision = assertions[check['name']]
        if not isinstance(decision, dict) or decision.get('status') not in ('PASS', 'FAIL', 'NOT_OBSERVED'):
            raise ValueError(f'Invalid status for {check["name"]}')
        reason = decision.get('reason')
        if not isinstance(reason, str) or not reason.strip(): raise ValueError('Every decision needs a reason')
        refs = (_evidence(folder, decision.get('evidence')) if decision['status'] != 'NOT_OBSERVED'
                else _evidence(folder, decision['evidence']) if decision.get('evidence') else [])
        if (run['case_id'] == 'G09' and check['name'] == 'independent_review_completed'
            and decision['status'] == 'PASS' and not _has_completed_review_event(folder, refs)):
            raise ValueError('G09 passing review needs a cited independent review-completed event and actual diff')
        graded.append({'name': check['name'], 'status': decision['status'], 'evidence': reason,
                       'evidence_refs': refs})
    if len(names) != len(set(names)) or set(names) != {check['name'] for check in graded if check['name'] in names}:
        raise ValueError('Run assertions do not match the current rubric')
    run['acceptance_checks'] = [c for c in graded if c['name'] not in activation_names]
    run['activation_checks'] = [c for c in graded if c['name'] in activation_names]
    if run['result'] != 'RUNNER_ERROR':
        run['result'] = scored_status(run['acceptance_checks']) if behavior_names else 'NOT_OBSERVED'
        run['activation_result'] = scored_status(run['activation_checks'], applicable=bool(activation_names))
    validate_record('eval-run', run)
    assessment = {'schema': 2, 'rubric_version': RUBRIC_VERSION, 'activation_result': run['activation_result'], 'case_id': run['case_id'], 'condition': run['condition'],
                  'reviewer': reviewer, 'result': run['result'],
                  'source_run_sha256': hashlib.sha256(run_bytes).hexdigest(),
                  'source_manifest_sha256': manifest_hash,
                  'source_environment_sha256': hashlib.sha256((folder / 'environment.json').read_bytes()).hexdigest(),
                  'assessment_kind': 'human-reviewed; evidence presence and hashes checked, interpretation not verified',
                  'assertions': [check for check in graded if check['name'] in names]}
    # Both files are new. Existing evidence and original run.json are never replaced.
    if (folder / 'graded-run.json').exists() or (folder / 'grading.json').exists():
        raise FileExistsError('This run already has a grade')
    _json(folder / 'grading.json', assessment)
    _json(folder / 'graded-run.json', run)
    write_grade_manifest(folder)
    return assessment


def load_graded(folder: Path):
    """Reject a grade if its source run or cited evidence changed after review."""
    folder = folder.resolve()
    manifest_hash = verify_manifest(folder)
    verify_grade_manifest(folder)
    raw = (folder / 'run.json').read_bytes()
    original = json.loads(raw)
    validate_record('eval-run', original)
    assessment = json.loads((folder / 'grading.json').read_text())
    graded = json.loads((folder / 'graded-run.json').read_text())
    if assessment.get('source_manifest_sha256') != manifest_hash:
        raise ValueError('Graded source manifest changed')
    environment = json.loads((folder / 'environment.json').read_text())
    timing = json.loads((folder / 'timing.json').read_text())
    if original['resource_measurement']['elapsed_seconds'] != timing['elapsed_seconds']:
        raise ValueError('Resource elapsed time disagrees with timing evidence')
    if original['resource_measurement'] != _usage((folder / 'stdout.ndjson').read_bytes(), environment.get('adapter_kind'), original['resource_measurement']['elapsed_seconds']):
        raise ValueError('Resource measurement disagrees with trace')
    if assessment.get('schema') != 2 or assessment.get('rubric_version') != RUBRIC_VERSION:
        raise ValueError('Incompatible grading rubric version')
    if hashlib.sha256(raw).hexdigest() != assessment['source_run_sha256']:
        raise ValueError('Graded source run changed')
    if hashlib.sha256((folder / 'environment.json').read_bytes()).hexdigest() != assessment['source_environment_sha256']:
        raise ValueError('Graded environment changed')
    if (graded['case_id'], graded['condition'], graded['result']) != (assessment['case_id'], assessment['condition'], assessment['result']):
        raise ValueError('Grading and result identity differ')
    if any(graded[k] != v for k, v in original.items() if k not in ('result', 'acceptance_checks', 'activation_result', 'activation_checks')):
        raise ValueError('Graded record changed source metadata')
    case = load_case(original['case_id'])
    behavior_names, activation_names = rubric_names(case, original['condition'])
    names = behavior_names + activation_names
    if set(names) != {c['name'] for c in assessment['assertions']}:
        raise ValueError('Graded assertions do not match the rubric')
    if json.loads((folder / 'environment.json').read_text()).get('case_sha256') != _case_hash(case):
        raise ValueError('The case or grading rubric changed since review')
    all_checks = graded['acceptance_checks'] + graded['activation_checks']
    if len({c['name'] for c in all_checks}) != len(all_checks): raise ValueError('Duplicate checks')
    checks = {c['name']: c for c in all_checks}
    for check in assessment['assertions']:
        if checks.get(check['name']) != check: raise ValueError('Graded assertion changed')
        if check['status'] not in ('PASS', 'FAIL', 'NOT_OBSERVED') or not check['evidence'].strip():
            raise ValueError('Invalid graded assertion')
        if check['status'] != 'NOT_OBSERVED' and not check['evidence_refs']:
            raise ValueError('Graded assertion lacks evidence')
        for ref in check['evidence_refs']:
            verified = _evidence(folder, [{k: ref[k] for k in ('path', 'start_line', 'end_line')}])[0]
            if verified['sha256'] != ref['sha256']: raise ValueError('Grading evidence changed')
        if (original['case_id'] == 'G09' and check['name'] == 'independent_review_completed'
            and check['status'] == 'PASS' and not _has_completed_review_event(folder, check['evidence_refs'])):
            raise ValueError('G09 passing review needs a cited independent review-completed event and actual diff')
    original_names = {x['name'] for x in assessment['assertions']}
    if [x for x in graded['acceptance_checks'] if x['name'] not in original_names] != [x for x in original['acceptance_checks'] if x['name'] not in original_names]:
        raise ValueError('Deterministic checks changed')
    if {c['name'] for c in graded['activation_checks']} != set(activation_names):
        raise ValueError('Activation checks do not match condition rubric')
    expected = ('RUNNER_ERROR' if original['result'] == 'RUNNER_ERROR' else
                scored_status(graded['acceptance_checks']) if behavior_names else 'NOT_OBSERVED')
    expected_activation = ('RUNNER_ERROR' if original['result'] == 'RUNNER_ERROR' else
                           scored_status(graded['activation_checks'], applicable=bool(activation_names)))
    if graded['activation_result'] != expected_activation or assessment.get('activation_result') != expected_activation:
        raise ValueError('Activation result does not match its evidence')
    if graded['result'] != expected: raise ValueError('Graded result does not match its evidence')
    validate_record('eval-run', graded)
    return graded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True, help='One condition directory from an eval run')
    parser.add_argument('--annotations', type=Path, required=True, help='Human-reviewed assertion decisions')
    args = parser.parse_args()
    try: result = grade(args.run, json.loads(args.annotations.read_text()))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f'grading error: {exc}\n')
    print(json.dumps(result, indent=2))
    return 0 if result['result'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
