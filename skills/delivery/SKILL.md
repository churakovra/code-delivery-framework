---
name: delivery
description: Route authorized repository work to a focused workflow and report evidence-based status. Use for actionable code, configuration, or documentation changes.
---

## Scope
Own delivery coordination and user intent.
## Context and competencies
Read applicable repository instructions and the current diff. Identify the next verifiable outcome and keep a compact checkpoint for multi-stage work: objective, branch/dirty baseline, ownership, settled decisions, acceptance, evidence, blockers, and next action. Adapt effort to risk: low work may remain in one loop; ordinary implementation includes focused checks and self-review; high-risk work requires an independent read-only reviewer and relevant integration or compatibility evidence. QA is optional when a distinct acceptance-to-check mapping helps. Planning and design are optional when complexity warrants them. For unresolved consequential behavior, use `../decision-interview/SKILL.md`; otherwise resolve routine choices directly.

Load only the skill relevant to the assigned work: `../implementation/SKILL.md` for general code, `../backend-development/SKILL.md` for server/data contracts, `../frontend-development/SKILL.md` for UI behavior, `../interface-design/SKILL.md` for design choices, `../debugging/SKILL.md` for a failure, `../documentation/SKILL.md` for docs, `../verification/SKILL.md` for distinct verification, and `../code-review/SKILL.md` for independent review. Planning can load `../planning/SKILL.md`. Do not read unrelated skills by default.

Delegate only when parallel work, fresh context, or an independent review materially helps. State why delegation is useful and assign bounded files/responsibility, objective, settled decisions, acceptance, baseline/unrelated edits, checks, blockers, and expected output using `../../templates/ownership-brief.md` when available. Tell agents to preserve other edits and coordinate overlap. Do not nest delegation; keep the delegation tree at most two levels deep.

For structural code exploration, follow repository instructions. A graph/memory integration may be used when available and applicable; it is optional elsewhere, and a missing graph is not a reason to block ordinary work.

Do not initiate exploratory browser walkthroughs or screenshot-based acceptance unless the user requests them. Required automated browser suites still apply; the user performs hands-on UX acceptance.
## Objective
Complete the authorized change and provide an auditable handoff.
## Edit permissions
Edit only assigned files; preserve unrelated changes. User retains commits, pull requests, merges, releases, and deployment unless expressly authorized.
## Evidence
Track branch and dirty baseline, requirements, changed files, checks and raw results, reviews, limitations, and manual acceptance. When reporting skill use or delegated work, distinguish trace-visible evidence from inference or a self-claim. Never promote a stale or delegated claim without inspecting evidence.
## Stopping
After two unsuccessful repair cycles for one acceptance failure, stop, preserve evidence, and obtain independent diagnosis before another fix. Report missing required checks or reviewers as blocked.
