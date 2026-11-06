#!/usr/bin/env python3
"""Run or preflight one CDF comparison using an explicitly supplied adapter."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evals import runner


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', required=True, help='Golden case ID, e.g. G01')
    p.add_argument('--conditions', nargs='+', choices=runner.CONDITIONS, default=list(runner.CONDITIONS))
    p.add_argument('--adapter', type=Path, required=True, help='Absolute executable path')
    p.add_argument('--adapter-kind', choices=('external', 'codex'), default='external')
    p.add_argument('--adapter-protocol', choices=('prompt-v1', 'json-dialogue-v1'), default='prompt-v1',
                   help='Protocol implemented by the supplied adapter; dialogue capability is operator-asserted')
    p.add_argument('--adapter-capabilities', type=Path, help='External adapter capability declaration JSON')
    p.add_argument('--output', type=Path, help='A new results directory')
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--timeout', type=int, default=300)
    p.add_argument('--model', help='Candidate request for Codex adapter, not confirmation')
    p.add_argument('--effort', help='Candidate reasoning effort for Codex adapter, not confirmation')
    p.add_argument('--preflight', action='store_true', help='Inspect requirements without running an adapter')
    p.add_argument('--allow-model-runs', action='store_true', help='Explicitly authorize adapter execution')
    args = p.parse_args()
    if args.timeout < 1 or args.seed < 0 or len(set(args.conditions)) != len(args.conditions):
        p.error('timeout must be positive, seed nonnegative, conditions unique')
    if args.adapter_kind != 'codex' and (args.model or args.effort):
        p.error('--model and --effort apply only to the Codex adapter')
    if not args.preflight and (not args.allow_model_runs or not args.output):
        p.error('running requires --allow-model-runs and a new --output directory')
    try:
        declaration = json.loads(args.adapter_capabilities.read_text()) if args.adapter_capabilities else None
        if args.preflight:
            result = runner.preflight(args.case, args.conditions, args.adapter, args.adapter_kind, args.adapter_protocol, declaration)
        else:
            result = runner.run(args.case, args.conditions, args.adapter, args.adapter_kind,
                                args.output.resolve(), args.seed, args.timeout, args.model, args.effort, args.adapter_protocol, declaration)
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    if args.preflight: return 0
    return 1 if any(r['result'] in ('FAIL', 'RUNNER_ERROR', 'BLOCKED') for r in result) else 0


if __name__ == '__main__':
    raise SystemExit(main())
