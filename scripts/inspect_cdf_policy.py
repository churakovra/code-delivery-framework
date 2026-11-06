#!/usr/bin/env python3
"""Read an explicitly selected advisory policy; never launch or configure agents."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cdf_runtime.policy import load_policy, delegation_decision, resolve_child


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--policy', type=Path, required=True)
    p.add_argument('--risk', choices=('LOW', 'MEDIUM', 'HIGH'), required=True)
    p.add_argument('--active-workers', type=int, default=0)
    p.add_argument('--authorized-worker-limit', type=int, help='Explicit operator authorization overriding the default worker budget')
    p.add_argument('--benefit', action='store_true')
    p.add_argument('--patch-ready', action='store_true')
    p.add_argument('--material-questions', action='store_true')
    p.add_argument('--shared-contract-changed', action='store_true')
    p.add_argument('--weak-failure-evidence', action='store_true')
    p.add_argument('--uncertain-rollback', action='store_true')
    p.add_argument('--reviewer-unavailable', action='store_true')
    p.add_argument('--role', choices=('worker', 'explorer', 'cdf_reviewer', 'cdf_diagnostician'), default='worker')
    p.add_argument('--tier', choices=('t0', 't1', 't2', 't3'), default='t1')
    args = p.parse_args()
    try:
        policy = load_policy(args.policy)
        decision = delegation_decision(policy, risk=args.risk, active_workers=args.active_workers,
                                       benefit=args.benefit, reviewer_available=not args.reviewer_unavailable,
                                       authorized_worker_limit=args.authorized_worker_limit,
                                       patch_ready=args.patch_ready, material_questions=args.material_questions,
                                       shared_contract_changed=args.shared_contract_changed,
                                       weak_failure_evidence=args.weak_failure_evidence,
                                       uncertain_rollback=args.uncertain_rollback)
        resolution = resolve_child(policy, role=args.role, tier=args.tier,
                                   reviewer_available=not args.reviewer_unavailable,
                                   review_required=decision['review_required'])
        print(json.dumps({'decision': decision, 'model': resolution.to_dict(),
                          'runtime_capabilities': 'not_probed', 'agents_launched': 0}, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'state': 'error', 'message': str(exc)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
