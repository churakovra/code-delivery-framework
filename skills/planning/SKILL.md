---
name: planning
description: Turn a requested outcome into a concise actionable plan when scope or sequencing needs resolution. Use before substantial or cross-component work.
---

## Scope
Plan the work; do not implement unless asked.
## Context and competencies
Inspect instructions, structure, and existing decisions. Consider data shapes, invariants, dependencies, generated artifacts, and verifiable increments. Separate settled requirements from unknown constraints, behavior and acceptance. Load `../decision-interview/SKILL.md` for substantial work or consequential unresolved choices.

For structural discovery, tracing or impact analysis, check for codebase-memory and its MCP; use them when available and suitable. Verify material findings against source. Fall back to source search for insufficient coverage or unavailable tools.
## Objective
For substantial work, decompose the outcome into bounded responsibilities with dependencies and non-overlapping ownership. Map each acceptance criterion to focused checks, including integration, regression or smoke checks when relevant. Identify which work can proceed in parallel, which needs independent review, and which skills or tools add value. Consider delegation against runtime restrictions and coordination cost. Give an ordered plan with owners, observable acceptance, checks, risks, and dependencies. Keep routine choices with the implementer.
## Edit permissions
Planning is read-only unless the user requested a durable planning artifact.
## Evidence
Cite inspected files and distinguish facts from assumptions. Identify unavailable tools or checks.
## Stopping
Stop when the plan is actionable. Do not repeatedly replan a settled brief.

## Conditional helpers
- Read `../helpers/communication.md` only for: Ambiguity-sensitive instructions or agent handoffs.
