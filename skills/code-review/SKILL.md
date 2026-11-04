---
name: code-review
description: Independently inspect a proposed change for concrete correctness, regression, and contract risks. Use for review requests and required independent review.
---

## Scope
Read-only review of the requested artifact against requirements and source. Establish whether it is a repository, branch, commit, pull request, or working-tree diff; inspect the corresponding changes when applicable.
## Context and competencies
Trace affected callers, dependency boundaries, and failure paths. Check whether abstractions preserve clear ownership and whether tests exercise observable behavior. For structural changes, assess whether behavior-preserving refactoring is supported by tests; suggest such refactoring only to resolve a concrete defect or clarity issue. Prioritize actionable defects with file/line evidence; distinguish blockers from suggestions. Required review must be independent of implementation. Recheck substantive repairs against the updated diff.
## Objective
Return findings or clearly state none, with inspected scope and evidence.
## Edit permissions
Do not edit implementation or tests. Do not trust implementer summaries in place of raw diff and results.
## Evidence
Inspect the brief, requested scope, relevant source, applicable complete diff, and actual check results.
## Stopping
Stop after complete scoped review; do not expand into speculative rewrites.

## Conditional helpers
- Read `../helpers/verification.md` only for: Assessing whether reported checks support a claim.
- Read `../helpers/accessibility.md` only for: Changed interactive UI or an explicitly requested accessibility review.
- Read `../helpers/react.md` only for: React or Next.js code with relevant rendering, fetching, or performance concerns.
