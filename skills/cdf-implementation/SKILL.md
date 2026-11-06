---
name: cdf-implementation
description: Implement an approved, bounded code or configuration change using the existing project's conventions and reusable modules. Use for any authorized code edit; combine with backend or frontend skill only when applicable.
---
# Implementation discipline

## Before edits
Confirm the outcome and acceptance; invoke `cdf-requirements` if a material user decision remains. Inspect local instructions, current diff, implicated call sites, existing patterns and relevant tests. Do not overwrite unrelated work.

## Execute
1. Choose the smallest coherent change. Search for and prefer existing domain logic, utilities, dependencies and code patterns. Do not create generalized frameworks, new layers or configuration knobs without a demonstrated need.
2. Preserve compatibility, validated assumptions, ownership boundaries, error semantics and cleanup. Coordinate shared API/data changes before parallel edits.
3. Keep code readable: names expose intent; functions have a coherent responsibility; avoid hidden effects and needless indirection. Follow repository style rather than imposing a universal preferred architecture.
4. For behavior changes, add or update a test at the owning behavior boundary when useful. Reproduce the bug with a failing test first when practical; do not fabricate a RED phase. Use project tools for formatting/type checks instead of repetitive prose reasoning.
5. Inspect the actual diff for stray edits and failure paths. Call `cdf-verification`; request `cdf-code-review` when risk warrants it.
6. Update docs only when a maintained contract, workflow or operational behavior changed. Never stage, commit, publish or deploy without applicable authorization.

## Exit
Report changed areas, fresh checks, unresolved assumptions and remaining acceptance gaps. Do not claim tests ran unless raw results support it.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `superpowers-tdd`: stateful behavior or regression suited to an explicit red/green/refactor cycle.
- `ub-mode`: complex incremental refactoring where its small-step principles clarify choices; do not import mandatory rituals.
- `superpowers-receiving-review`: difficult or contradictory review feedback; verify each proposed change.
Fallback: focused behavior-first changes and diff inspection above.
