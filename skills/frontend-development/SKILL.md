---
name: frontend-development
description: Implement user-facing web or application interfaces within established product conventions. Use when changing frontend behavior or presentation.
---

## Scope
Frontend implementation; pair with `interface-design` only when a design decision is needed.
## Context and competencies
Inspect existing production components, semantic design tokens, routes, responsive behavior, and accessibility patterns. Tests and stories should exercise the real production component rather than a duplicate implementation. Prefer local conventions and minimal dependencies. Cover meaningful interaction states, such as loading, empty, error, or disabled states when applicable. Apply framework-specific guidance only when that stack is actually present.
## Objective
Deliver the requested interaction and responsive states with observable checks.
## Edit permissions
Edit assigned UI files and focused tests. Do not initiate exploratory browser walkthroughs unless requested; required automated browser suites still apply.
## Evidence
Run relevant unit, type, lint, build, and required browser checks; report what was actually run.
## Stopping
Escalate unresolved product behavior; stop after two failed repair cycles for independent diagnosis.
