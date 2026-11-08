---
name: cdf-requirements
description: Determine implementation readiness and resolve consequential product, business, API and behavior decisions before changing code. Use for ambiguous feature requests, behavior changes and unclear acceptance; do not interrogate fully specified routine edits.
---
# Requirements and decision gate

## Contract
Do not start edits that depend on unresolved **material** decisions. Recommendations and guesses are not user decisions. The user's established choices and repository evidence count as known; do not ask again. Technical implementation details and numeric tuning within an approved contract belong to the engineer. Preserve adjacent behavior unless changing it is necessary within accepted intent; agree material scope expansion before dependent edits.

## Method
1. Classify the request as exploration, explanation, implementation, or explicit design/plan. Do not implement exploratory language as authorization.
2. Inspect the relevant current behavior, documented contracts, tests, callers and constraints before asking questions. Separate **observed facts**, **user-confirmed decisions**, **routine defaults**, and **unknowns**.
3. Create a small decision dependency graph. Label each unknown: **blocking/material** if it changes externally observable behavior, permissions, data loss, compatibility, business rules, deadlines or significant cost; **routine** if the engineer can safely choose without changing intent.
4. Ask all currently answerable material questions together when practical. For each, give concrete alternatives, tradeoffs and a recommendation without assuming acceptance. Ask dependent questions only after prerequisites are answered. Preserve answers across turns and handoffs.
5. Define a compact acceptance contract: intended behavior, boundaries/non-goals, actors, failure/edge behavior, compatibility, observable success at the user-facing boundary, preserved adjacent behavior, checks, and unresolved blockers. A short in-context checkpoint is enough; create an artifact only for long or requested work.
6. Proceed with dependent edits only when material decisions are resolved or the user explicitly accepts a stated default. Independent read-only investigation can continue earlier. Reopen this gate only if the scope changes or new material ambiguity is discovered.

## Exit
**READY**: behavior and acceptance can be implemented without inventing a user decision. **BLOCKED**: list only remaining material questions and safely independent next steps. **EXPLORATORY**: answer/plan; do not edit.

## Reference on demand
- `references/interview-patterns.md` when the decision tree is large, consequential or needs a durable checkpoint.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `matt-grilling`: multilevel dependent business decisions; use rounds, not compulsory relentless questioning.
- `superpowers-brainstorming`: uncertain product direction or large design alternatives; adapt its approval step to user authority and task size.
Fallback: the decision-graph method above. Load neither for small, well-specified edits. Never auto-install subskills.
