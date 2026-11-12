# Adaptive delivery

Distinguish explain/explore/audit/plan from implement/operate. Read-only work and a plan do not authorize code changes. Implementation does not authorize publication or global configuration changes.

- SIMPLE: a known local, low-risk change → inspect the relevant context, edit, focused check, diff inspection. No mandatory plan, question, child or full suite.
- STANDARD: connected modules or meaningful uncertainty → compact acceptance in context, reversible increments ordered by dependencies, relevant contract/integration checks and risk-based review.
- COMPLEX: authorization, sensitive data, migrations, concurrency or difficult rollback → explicit invariants and alternatives, resolve material choices, validate adverse paths and obtain independent review.

Change mode when evidence changes risk. A file count or the word API does not determine complexity. Prefer established helpers and conventions; coordinate shared contracts before parallel edits. A plan records outcome, boundaries, dependencies and acceptance-to-check mapping, not a new runtime.

## Adaptive strategy selection

Choose the shortest justified path to the accepted outcome. Identify the main uncertainty, then choose an action that advances the outcome or resolves that uncertainty in proportion to risk and cost. Do not resolve every unknown up front or turn this loop into a required checklist or artifact. These are starting strategies, not mandatory workflows:

| Task | Starting strategy | Earliest credible evidence |
| --- | --- | --- |
| Simple edit | Inspect local context, edit, focused check | Correct diff and relevant check |
| Bugfix | Reproduce, discriminate causes, repair | Original symptom gone on the active path; regressions preserved |
| New functionality | Small complete vertical scenario, verify, expand | Working end-to-end user scenario |
| API | Existing contracts, one working request path, expand | Real request/response, errors and authorization |
| Frontend/UI | User goal, core interaction, visual assessment | Working interaction in the opened interface; visual quality assessed separately |
| Refactoring | Establish behavior, incremental changes, verify | Required behavior preserved without unnecessary abstractions |
| Database migration | Invariants and risks, safety evidence, controlled change | Compatibility, recovery and constraints checked before risky execution |
| Architecture | Research, riskiest hypothesis, experiment | Evidence for the consequential architectural assumption |
| Read-only research | Relevant evidence, grounded answer | Accurate sourced answer without workspace changes |

For new functionality, identify the smallest complete user scenario and implement it through real integration boundaries. Check that it solves that part of the request, retain discovered limitations, then expand to the remaining requirements. A vertical slice is an intermediate checkpoint, never permission to abandon accepted scope. Debugging, refactoring and migrations need their own evidence rather than a compulsory prototype.

## Early feedback and reassessment

Prefer the earliest credible check of the most consequential assumption. Minimize unnecessary work and the risk of building on an untested premise, rather than simply minimizing actions. A narrow experiment can be more useful than broad speculative research. Cheap isolated unit tests cannot replace necessary integration, safety or acceptance checks.

After meaningful evidence, reconsider progress toward the outcome, the main remaining uncertainty and the next useful action. Change approach when a hypothesis fails; user rejection is new evidence even with green tests. If only an intermediate slice works, continue the remaining scope. If an action neither resolves material uncertainty nor improves acceptance, omit it. Stop when all accepted requirements and required evidence are satisfied, without extra rituals. A real blocker requires a precise missing decision, permission or capability; preserve useful work and continue independent authorized work. No fixed command, test or time count determines completion.

For continuity retain accepted intent/scope, decision sources, branch/HEAD, evidence freshness, failed attempts, open questions and next step. Keep this in context unless a durable handoff needs a file. Recheck affected facts after revision or scope changes.

User rejection is new outcome evidence even with green tests. After the first rejection reconcile the active path/version/configuration and prior checks. After two failed repairs use a different discriminating experiment or independent diagnosis before another dependent edit; use cdf-debugging for the method. Distinguish a new requirement from an unsuccessful repair.

Before another search, tool, skill, child or test suite identify the uncertainty it closes. Stop when contracts, reuse and acceptance are sufficiently grounded. Expand checks for risk, new changes or failures; do not truncate critical evidence to save tokens or repeat broad checks without a reason.

## Deliverables and native progress

Exploration is an intermediate step when the user requested an artifact or operation. Continue through the authorized implementation and its verification; a research summary does not replace that result. After negative feedback, reproduce the original user action and identify which evidence layer failed before changing the hypothesis.

Use supported host commentary/progress and a native plan when available and useful. Briefly state verified progress toward the outcome and the purpose of the next action at meaningful checkpoints: evidence changed, a hypothesis failed, work is blocked, or a result was verified. For example: “The main API flow passes; checking authorization and errors before delivery.” Activity is not confirmed progress. Do not invent percentages, repeat empty updates or add a status server, daemon, repository log or mandatory plan artifact. A skill cannot guarantee control of a particular host UI line; report that limitation when it matters. Tiny changes need no progress ritual.
