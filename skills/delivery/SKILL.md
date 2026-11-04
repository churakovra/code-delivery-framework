---
name: delivery
description: Coordinate repository work, choose roles and conditional helpers, and enforce evidence and shipping gates.
---

## Coordinate the task
Read project instructions and the diff. Checkpoint objective, branch/dirty baseline, acceptance, ownership, risk, evidence, and next action. Small tasks need no plan artifact. Higher-priority instructions prevail; preserve user-owned skills and edits.

For repository exploration or understanding, audits, cleanup, architecture, dependencies, or impact analysis, follow `../helpers/codebase-memory.md` before structural exploration, including without planning or delegation.

Act, inspect evidence, update the checkpoint, and repeat. Integrate subagent findings. A failed approach or partial milestone is not a reason to stop while useful authorized work remains. Reassess user input; preserve the objective unless changed or stopped.

For learning, explain the next concept, offer a step, and review the work; adapt when asked to implement. For implementation readiness, follow `../decision-interview/SKILL.md`. For substantial work, load planning and establish outcome, constraints and acceptance; existing answers and evidence can satisfy the interview without new questions. Continue independent work; keep dependent work pending when an answer is required. Resume on the answer; elapsed time is not an answer. Finish when acceptance is evidenced, the user stops or changes the work, or a concrete blocker prevents meaningful authorized progress. Report blockers and evidence.

## Select and delegate
Before work, decompose the task into responsibilities and dependencies. Choose direct work, a sequence of role-assigned subagents, or a mix within runtime restrictions; keep simple decomposition informal and revisit it when the task changes. Work directly by default using the current chat model; apply the relevant role composition from `.codex/delivery-framework/roles.json` under the framework target to direct work too. Delegate bounded independent work when its expected benefit exceeds coordination and token costs. Load applicable implementation and verification skills, planning for unresolved sequencing, and conditional helpers only when applicable.

For specialist work, read `../helpers/specialist-routing.md` to select specialist candidates for direct and delegated work.

Delegate for independent review, useful parallel ownership, specialist work, or independent diagnosis after two failed repairs. Only the master agent launches agents; subagents request follow-up from it. Keep two levels maximum. Settle shared contracts first; assign bounded ownership and request evidence, uncertainty, and findings. Wait for results, reconcile and inspect integrated work, and assign repairs or follow-up. For consequential designs, seek an early independent design check when available; it does not replace review of the actual diff. If delegation is unavailable, work directly where possible and state why required review is unavailable.

Before launch, read `../helpers/delegation.md`. For a fixed role, compare its runtime-advertised model and reasoning effort with both policy values; distinguish a request from a confirmed active setting. If a matching launch is unavailable, treat that delegation as unavailable.

## Review and completion
Low risk is local, simple behavior; medium risk includes cross-component behavior or nontrivial failure handling; high risk includes authentication, permissions, money, persistence integrity, migrations, shared contracts, concurrency, and broad lifecycle changes. Require independent review for medium/high risk OR more than three changed code files OR more than 50 added/deleted code lines. Exclude generated files and documentation. Behavioral risk overrides size. Review the actual diff, callers, failure paths, and check output. Substantive repairs require updated review.

Use project-authoritative checks and meaningful regression coverage; never weaken assertions to pass. Verify UI changes with bounded local visual and interaction checks when needed and permitted; respect external-action boundaries. After two failed repairs, obtain independent diagnosis before another fix. If required review is unavailable, finish the authorized patch and checks, then mark shipping blocked.

For feature work, branch operations, or requested commits, read `../helpers/git-workflow.md`; respect higher-priority branch restrictions. Preserve explicit authorization for staging, commits, pull requests, publishing, merges, releases, and deployment. Report outcome, changed files, checks, review status, and material gaps. Include manual acceptance only when applicable.
