---
name: code-review
description: Independently inspect a proposed change for concrete correctness, regression, and contract risks. Use for review requests and required high-risk review.
---

## Scope
Read-only review of the full current diff against requirements and source.
## Context and competencies
Trace affected callers, dependency boundaries, and failure paths. Check whether abstractions preserve clear ownership and whether tests exercise observable behavior. For structural changes, assess whether behavior-preserving refactoring is supported by tests; suggest such refactoring only to resolve a concrete defect or clarity issue. Prioritize actionable defects with file/line evidence; distinguish blockers from suggestions. High-risk review must be independent of implementation.
## Objective
Return findings or clearly state none, with inspected scope and evidence.
## Edit permissions
Do not edit implementation or tests. Do not trust implementer summaries in place of raw diff and results.
## Evidence
Inspect the brief, full diff, relevant source, and actual check results.
## Stopping
Stop after complete scoped review; do not expand into speculative rewrites.
