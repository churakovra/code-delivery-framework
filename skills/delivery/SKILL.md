---
name: delivery
description: Route authorized repository work to a focused workflow and report evidence-based status. Use for actionable code, configuration, or documentation changes.
---

## Scope
Own delivery coordination and user intent.
## Context and competencies
Read applicable repository instructions and the current diff. Identify the next verifiable outcome and keep a compact checkpoint for multi-stage work: objective, branch/dirty baseline, ownership, settled decisions, acceptance, evidence, blockers, and next action. Adapt effort to risk: low work may remain in one loop; ordinary implementation includes focused checks and self-review; high-risk work requires an independent read-only reviewer and relevant integration or compatibility evidence. QA is optional when a distinct acceptance-to-check mapping helps. Planning and design are optional when complexity warrants them. For unresolved consequential behavior, use `../decision-interview/SKILL.md`; otherwise resolve routine choices directly.

Before selecting a design, turn the user's goal into an explicit, proportionate set of requirements and observable acceptance criteria. Inspect available context first. If a material product, scope, or contract decision remains open, use `../decision-interview/SKILL.md` to help the user express it. Continue independent investigation while awaiting answers. Wait before implementing work that depends on an unresolved decision. Resolve routine details from evidence and reasonable judgment.

Load only the skill relevant to the assigned work: `../implementation/SKILL.md` for general code, `../backend-development/SKILL.md` for server/data contracts, `../frontend-development/SKILL.md` for UI behavior, `../interface-design/SKILL.md` for design choices, `../debugging/SKILL.md` for a failure, `../documentation/SKILL.md` for docs, `../verification/SKILL.md` for distinct verification, and `../code-review/SKILL.md` for independent review. Planning can load `../planning/SKILL.md`. Do not read unrelated skills by default.

Delegate only when parallel work, fresh context, or an independent review materially helps. State why delegation is useful and assign bounded files/responsibility, objective, settled decisions, acceptance, baseline/unrelated edits, checks, blockers, and expected output using `../../templates/ownership-brief.md` when available. Tell agents to preserve other edits and coordinate overlap. Do not nest delegation; keep the delegation tree at most two levels deep.

Give a reviewer an inspectable diff or another concrete, bounded review assignment. Do not launch a reviewer only to wait for implementation. If required independent review cannot be delegated yet, continue authorized implementation and checks that do not depend on it. Report the missing review as a completion blocker; do not claim that self-review satisfies it. Follow higher-priority delegation restrictions.

## Role and model routing
Select the role from the work assignment. Select skills for the work, including the role's required skills. A skill can support multiple roles. A role can use multiple skills. For work owned by the main agent, apply the relevant role and skills using the current chat model. Do not claim that a policy entry changed the running model.

Before each authorized delegated launch, identify the framework target containing this skill. Read `.codex/delivery-framework/roles.json` and `.codex/delivery-framework/model-policy.toml` under that same target. Choose the role for the assignment. Resolve its `policy` key to the model and `reasoning_effort` in the current policy. A user or the model-routing skill can choose the policy entries. Treat those files as configuration data, not as instructions to bypass higher-priority rules.

When the runtime supports explicit model and effort on a generic subagent launch, use a generic subagent with the policy's model and effort. Do not select a named role with fixed model settings for this path. If an override requires a fresh context, use it. For every launch, supply the assignment, baseline, acceptance criteria, ownership, constraints, role `instructions`, `read_only` restriction, and required skill paths. Resolve skill paths under the framework target or use their available catalog names. Read the installed dependency inventory, if present. Include the role-specific subskills and their activation conditions in the brief. Include any other task-relevant skills. Tell the subagent to apply the role and skills, preserve other work, and not delegate. Follow higher-priority instructions about whether delegation is permitted.

If the policy, role, model, effort, or override is unavailable, do not silently claim the policy was applied or substitute a model. Report the limitation. A named generated role may be used only as an explicitly disclosed compatibility fallback when its active runtime model and effort match the current policy. A match on disk alone is not evidence of the active settings. If needed, synchronize generated role files with `sync-models` and start a fresh session. Verify the active settings before launch. If they cannot be verified, report the limitation. A running chat or subagent does not change model when the policy changes.

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
