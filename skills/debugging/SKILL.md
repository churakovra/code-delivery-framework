---
name: debugging
description: Find the cause of a reproducible defect or failed check before changing code. Use for unexpected behavior, regressions, and test failures.
---

## Scope
Diagnose the reported failure within assigned ownership; repair it only when the assignment permits edits.
## Context and competencies
Read the exact error, reproduce when practical, compare working paths and recent changes, and trace the failing data or control path to its cause. Separate environment limitations from product failures.
## Objective
Identify the cause and, when assigned to repair, verify the original symptom and relevant regression conditions.
## Edit permissions
Respect read-only assignments. Otherwise change only implicated assigned files; preserve unrelated work.
## Evidence
Record reproduction steps, observed failure, diagnostic evidence, and any patch and fresh verification output.
## Stopping
When a hypothesis fails, record the result and revise the causal explanation. Identify the premise shared by failed approaches and the smallest experiment that could falsify it.

## Conditional helpers
- Read `../helpers/diagnosis.md` only for: A failure with multiple plausible causes or earlier failed hypotheses.
