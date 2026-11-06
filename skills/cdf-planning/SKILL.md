---
name: cdf-planning
description: Turn a settled, nontrivial software change into a bounded implementation sequence with dependencies, ownership, acceptance and checks. Use for multi-component changes, risky migrations or explicit planning; skip plan artifacts for tiny clear edits.
---
# Task planning

## Preconditions
Apply `cdf-requirements` when material behavior is unknown. A plan is not permission to choose business behavior. Inspect the actual code and conventions, not only the feature description.

## Method
1. Specify the outcome, non-goals, confirmed decisions, baseline and observable acceptance.
2. Identify affected contracts, files/modules and invariants; check existing implementations and reuse before proposing new abstractions.
3. Choose the smallest reversible increments. Put interfaces and shared data contracts before parallel work; map each acceptance item to evidence (unit, integration, compatibility, UI or manual acceptance).
4. Mark sequencing dependencies and file ownership. By default the master can execute the plan in one context; delegation is only a conditional optimization evaluated by `cdf-orchestration`.
5. Identify risk hotspots, migration/rollback considerations and authorization boundaries. Escalate unresolved material choices to the user, not a subagent.
6. Output an actionable short plan. Use exact paths only when inspected and stable. Avoid copying large code snippets, creating ceremonial project documents or replanning settled work.

## Exit
A capable engineer can implement without inventing product behavior, and each step has an observable completion condition.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `superpowers-writing-plans`: large, multi-step execution needing explicit file/check instructions; avoid its verbose format for routine work.
- `wsh-task-coordination`: many truly independent workstreams or dependency graphs.
Fallback: steps with owner, dependencies, acceptance and checks as above.
