---
name: delivery
description: Coordinate repository work, choose roles and conditional helpers, and enforce evidence and shipping gates.
---

## Coordinate the task
Read project instructions and the diff. Checkpoint objective, branch/dirty baseline, acceptance, ownership, risk, evidence, and next action. Small tasks need no plan artifact. Higher-priority and explicit user instructions prevail; preserve user-owned skills and edits.

Maintain the objective across turns. Execute the next action, inspect evidence, update the checkpoint, and repeat. Integrate subagent findings. A failed approach or partial milestone is not a reason to stop while useful authorized work remains. Reassess user input without abandoning the objective unless changed or stopped.

Ask when information, a consequential decision, or authorization is needed. Any agent may ask the user when permitted or relay questions to the master agent. Continue independent work; keep dependent work pending. Resume on the answer; elapsed time is not an answer. Finish when acceptance is evidenced, the user stops or changes the work, or a concrete blocker prevents meaningful authorized progress. If blocked, report the blocker, evidence, and next action.

## Select and delegate
Before work, decompose the task to identify responsibilities, dependencies, and useful delegation. The master agent chooses direct work, a sequence of role-assigned subagents, or a mix, subject to runtime restrictions. Keep simple decomposition informal; revisit it when the task changes. Work directly by default using the current chat model. Load only applicable implementation, backend, frontend, interface-design, debugging, documentation, verification, or code-review skills. Load planning for unresolved sequencing and decision-interview for consequential choices evidence cannot answer. Roles load helpers only when their activation conditions match; consult the installed `.codex/delivery-framework/subskills.json` only to resolve dependencies.

For specialist work, read `../helpers/specialist-routing.md` to select optional skills for direct and delegated work.

Delegate for independent review, useful parallel ownership, specialist work, or independent diagnosis after two failed repairs. Only the master agent launches agents; subagents request follow-up from it. Keep two levels maximum. Wait for relevant results, inspect evidence, and assign follow-up or repair findings. If delegation is prohibited or unavailable, work directly where possible and disclose unavailable required review.

Before launch, read `.codex/delivery-framework/roles.json` and `model-policy.toml` under the framework target. Resolve the role's policy key. Use a generic agent with explicit model/effort when supported and fresh context when required. Supply role instructions, skill paths, applicable helpers and specialist candidates, read-only constraints, objective, ownership, baseline, acceptance, locations, and evidence. Ask the subagent to verify candidate availability and use the fallback if absent. Preserve others' edits and prohibit nested delegation.

Before using a fixed named role, compare its runtime-advertised model and reasoning effort with both policy values; use it as a disclosed fallback only when both match. Disk configuration does not prove active settings. Record the role, policy, requested settings, and runtime evidence; distinguish a request from a confirmed active setting. If settings are unknown or mismatched and a matching explicit launch is unavailable, disclose this and treat that delegation as unavailable. Never silently substitute settings or claim a policy changed a running model.

## Review and completion
Low risk is local, simple behavior; medium risk includes cross-component behavior or nontrivial failure handling; high risk includes authentication, permissions, money, persistence integrity, migrations, shared contracts, concurrency, and broad lifecycle changes. Require independent review for medium/high risk OR more than three changed code files OR more than 50 added/deleted code lines. Exclude generated files and documentation. Behavioral risk overrides size. Review the actual diff, callers, failure paths, and check output. Substantive repairs require updated review.

Use project-authoritative checks and meaningful regression coverage; never weaken assertions to pass. Do not initiate exploratory browser walkthroughs or screenshot acceptance unless requested. After two failed repairs, obtain independent diagnosis before another fix. If required review is unavailable, finish the authorized patch and checks, then mark shipping blocked.

Preserve explicit authorization for staging, commits, branches, pull requests, publishing, merges, releases, and deployment. Report outcome, changed files, checks, review status, and material gaps. Include manual acceptance only when applicable.
