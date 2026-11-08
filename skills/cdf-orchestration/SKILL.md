---
name: cdf-orchestration
description: Coordinate multi-step repository delivery, decide direct execution versus bounded subagent delegation, apply risk gates and integrate results. Use for master-owned software work; do not create a subagent merely because a role exists.
---
# Single-agent-first delivery

## Ownership
The master owns requirements, user communication, integration and final result. A role is a responsibility profile and can be performed by the master. Runtime/user instructions override this workflow.

1. Check task intent and use `cdf-requirements` for unresolved material choices. Continue independent investigation but block dependent edits. Establish concise acceptance and current working-tree baseline.
2. Apply needed skills directly by default. Use `cdf-planning` only for nontrivial sequencing, `cdf-codebase-research` for uncertain structure and domain skills only for actual work. Avoid repeating reads already evidenced in context.
3. Delegate only when at least one measurable benefit is plausible: independently owned parallel work, disposable large research context, isolated specialist reasoning, or risk-relevant independent review/diagnosis. Compare coordination, repeated context and integration cost. Do not use line/file-count thresholds as the sole reason.
4. Before delegation settle shared contracts; assign narrow objective, scope/files, baseline, confirmed decisions, dependencies, acceptance and required evidence. Default to at most two simultaneously active delegated workers; a smaller selected operator budget applies. Exceed two only with explicit user authorization. Subagents do not spawn subagents. Verify runtime role/model availability; never infer active model from disk configuration.
5. Integrate actual changes, resolve collisions, run `cdf-verification` and request independent `cdf-code-review` for high-risk changes and meaningful medium-risk gaps. If mandatory independent review is unavailable, mark readiness BLOCKED_REVIEW; never substitute self-review. For medium risk, review shared-contract changes, weak failure evidence or uncertain rollback.
6. Reassess after new findings, material scope changes or repeated failures. Repeated user rejection of the same outcome activates `cdf-debugging`, even across turns with green tests. Preserve failed attempts and hypotheses in a compact in-context checkpoint; write a durable plan only when requested or continuity needs it.
7. Finish with outcome, changed surface, test evidence, review status and unresolved risk; avoid ceremonial summaries and unrelated docs.

## Reference on demand
- `references/delegation-contract.md` for an actual delegated assignment or disputed handoff.
- `references/operator-policy.md` when the operator supplies a model-routing policy; apply its worker budget, review preference and candidate/fallback rules before requesting a child. No supplied policy means current runtime settings and the two-worker default, not automatic model research.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `superpowers-executing-plans`: long dependent inline plan where compact checkpoints prevent omission.
- `superpowers-parallel-agents`: two or more truly independent workstreams, disjoint ownership and worthwhile parallelism.
- `wsh-task-coordination`: complex dependency graphs and several workers.
Fallback: stay in one context, work sequentially and verify.
