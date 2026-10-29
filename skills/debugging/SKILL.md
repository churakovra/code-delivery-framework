---
name: debugging
description: Find the cause of a reproducible defect or failed check before changing code. Use for unexpected behavior, regressions, and test failures.
---

## Scope
Diagnose and repair the reported failure within assigned ownership.
## Context and competencies
Read the exact error, reproduce when practical, compare working paths and recent changes, and trace the failing data or control path to its cause. Separate environment limitations from product failures.
## Objective
Repair the cause and verify the original symptom and relevant regression conditions.
## Edit permissions
Change only implicated assigned files; preserve unrelated work.
## Evidence
Record reproduction steps, observed failure, diagnostic evidence, patch, and fresh verification output.
## Stopping
After two failed repairs on the same acceptance failure, stop and obtain independent diagnosis. The diagnosis should state the shared premise behind the failed approaches and propose the smallest experiment that could falsify it before another repair.

## Conditional helpers
- Read `../helpers/diagnosis.md` only for: A reproducible bug, failed check, or unexpected behavior.
- Read `../helpers/regression-testing.md` only for: A behavior change or repair with a meaningful observable regression.
