---
name: delivery
description: Coordinate repository work, choose roles and conditional helpers, and enforce evidence and shipping gates.
---

## Coordinate
Read project instructions and the current diff. Keep one compact checkpoint: objective, branch/dirty baseline, observable acceptance, ownership, risk, current evidence, and next action. Small tasks need no separate plan artifact.

Use this skill once while its contents remain available. Reread after relevant changes or context loss. Delivery owns sequencing, delegation, review, escalation, and completion. Role skills own methods; helpers own narrow techniques. Higher-priority and explicit user instructions prevail. Preserve user-owned skills; use them when explicitly requested, and resolve conflicting workflow rules through instruction precedence.

## Select the next role
Work directly by default, using the current chat model. Load only the applicable skill relative to this directory: `../implementation/SKILL.md` for general changes, `../backend-development/SKILL.md` for server/data contracts, `../frontend-development/SKILL.md` for UI implementation, `../interface-design/SKILL.md` for substantial design decisions, `../debugging/SKILL.md` for failures, `../documentation/SKILL.md` for docs, `../verification/SKILL.md` for distinct verification, or `../code-review/SKILL.md` for independent review. Load planning only for unresolved sequencing; load decision-interview only for consequential choices evidence cannot answer.

Roles load named helpers only when their activation conditions match. Helpers are Markdown references, not separately triggered skills. Do not load every role dependency. The installed inventory `.codex/delivery-framework/subskills.json` under the framework target records paths and conditions; consult it only to resolve a dependency. The target contains `.agents`; a global target may differ from the working repository.

## Delegate selectively
Delegate for independent review, useful parallel ownership, specialist work, or independent diagnosis after two failed repairs of one acceptance failure. Only the main agent launches agents; subagents request follow-up work from it. Keep two levels maximum.

Before launch, read `.codex/delivery-framework/roles.json` and `model-policy.toml` under the framework target. Resolve the role's policy key. Use a generic agent with explicit model/effort when supported, with fresh context when required. Supply role instructions, required skill paths, conditional helpers, read-only constraints, objective, ownership, baseline, acceptance, relevant source locations, and current evidence. Avoid copying complete conversations. Preserve others' edits and prohibit nested delegation.

Never silently substitute unavailable settings or claim a policy changed a running model. A fixed named role is a disclosed fallback only when its active settings match the policy. Disk configuration alone proves no active settings.

## Review and completion
Low risk is local, simple behavior. Medium risk includes cross-component behavior or nontrivial failure handling. High risk includes authentication, permissions, money, persistence integrity, migrations, shared contracts, concurrency, and broad lifecycle changes.

Require independent review for medium/high risk OR more than three changed code files OR more than 50 added/deleted code lines. Exclude generated files and documentation from counts. Behavioral risk overrides size. Review the actual diff, callers, failure paths, and check output. Substantive repairs require updated review.

Use project-authoritative checks and meaningful regression coverage. Do not initiate exploratory browser walkthroughs or screenshot acceptance unless requested. Never weaken assertions to pass. After two failed repairs, obtain independent diagnosis before another fix. If required review is unavailable, finish the authorized patch and checks, then mark shipping blocked.

Preserve explicit authorization for staging, commits, branches, pull requests, publishing, merges, releases, and deployment. Report outcome, changed files, current checks, review status, and material gaps. Include manual acceptance only when applicable.
