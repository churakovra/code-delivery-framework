---
name: delivery
description: Coordinate repository work, choose roles and conditional helpers, and enforce evidence and shipping gates.
---

## Coordinate the task
Read project instructions and the diff. Checkpoint objective, branch/dirty baseline, acceptance, ownership, risk, evidence, and next action. Small tasks need no plan artifact. Higher-priority and explicit user instructions prevail; preserve user-owned skills and edits.

Maintain the objective across turns. Execute the next action, inspect evidence, update the checkpoint, and repeat. Integrate subagent findings. A failed approach or partial milestone is not a reason to stop while useful authorized work remains. Reassess user input without abandoning the objective unless changed or stopped.

When the user wants to learn, preserve their agreed participation: explain the next useful concept, offer a manageable step, and review their work. Adapt when they ask the agent to implement. For consequential lifecycle or contract choices, establish the operating behavior and material tradeoffs before dependent implementation; resolve routine choices directly.

For substantial work, load planning and conduct a short requirements interview before dependent implementation when permitted. Establish outcome, material constraints and acceptance; use existing user answers and repository evidence. Use structured questions when permitted. If prohibited, follow runtime rules and record assumptions. For smaller work, ask when needed. Continue independent work; keep dependent work pending when an answer is required. Resume on the answer; elapsed time is not an answer. Finish when acceptance is evidenced, the user stops or changes the work, or a concrete blocker prevents meaningful authorized progress. Report blockers and evidence.

## Select and delegate
Before work, decompose the task to identify responsibilities, dependencies, and useful delegation. The master agent chooses direct work, a sequence of role-assigned subagents, or a mix, subject to runtime restrictions. Keep simple decomposition informal; revisit it when the task changes. Work directly by default using the current chat model; delegate bounded independent work when its expected benefit exceeds coordination and token costs. Load applicable implementation and verification skills. Load planning for substantial work or unresolved sequencing, and decision-interview for the substantial-work interview or consequential choices evidence cannot answer. Roles load helpers only when their activation conditions match; consult the installed `.codex/delivery-framework/subskills.json` only to resolve dependencies.

For specialist work, read `../helpers/specialist-routing.md` to select specialist candidates for direct and delegated work.

Delegate for independent review, useful parallel ownership, specialist work, or independent diagnosis after two failed repairs. Only the master agent launches agents; subagents request follow-up from it. Keep two levels maximum. Wait for relevant results, inspect evidence, and assign follow-up or repair findings. If delegation is prohibited or unavailable, work directly where possible and disclose unavailable required review.

Parallelize independent investigations and non-overlapping implementation when permitted and worthwhile. Settle shared contracts first; give each agent a bounded question or ownership and request evidence, uncertainty, and findings. Reconcile results and inspect integrated work. For consequential designs, seek an early independent design check when available; it does not replace review of the actual diff. State the specific reason when required independent review is unavailable.

Before launch, read `../helpers/delegation.md`. For a fixed role, compare its runtime-advertised model and reasoning effort with both policy values; distinguish a request from a confirmed active setting. If a matching launch is unavailable, treat that delegation as unavailable.

## Review and completion
Low risk is local, simple behavior; medium risk includes cross-component behavior or nontrivial failure handling; high risk includes authentication, permissions, money, persistence integrity, migrations, shared contracts, concurrency, and broad lifecycle changes. Require independent review for medium/high risk OR more than three changed code files OR more than 50 added/deleted code lines. Exclude generated files and documentation. Behavioral risk overrides size. Review the actual diff, callers, failure paths, and check output. Substantive repairs require updated review.

Use project-authoritative checks and meaningful regression coverage; never weaken assertions to pass. Do not initiate exploratory browser walkthroughs or screenshot acceptance unless requested. After two failed repairs, obtain independent diagnosis before another fix. If required review is unavailable, finish the authorized patch and checks, then mark shipping blocked.

Preserve explicit authorization for staging, commits, branches, pull requests, publishing, merges, releases, and deployment. Report outcome, changed files, checks, review status, and material gaps. Include manual acceptance only when applicable.
