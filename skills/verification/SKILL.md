---
name: verification
description: Select and run checks that provide evidence for a change’s acceptance criteria. Use after implementation or when explicitly asked to verify.
---

## Scope
Verify independently of implementation conclusions.
## Context and competencies
Map each acceptance criterion to the smallest meaningful observable check. Select commands from project-authoritative guidance and choose the affected test layer. Read raw output and inspect current changes. Use mutation testing only when available and useful to assess whether behavior assertions detect a meaningful regression; no particular verification tool is mandatory. For high-risk work, include required integration/compatibility evidence.
## Objective
Report passed, failed, skipped, and unavailable checks with exact evidence.
## Edit permissions
Verification is read-only; do not change code or weaken assertions to obtain a pass.
## Evidence
Fresh output is required for claims. A report from another agent is not itself evidence.
## Stopping
Stop when criteria are evidenced or precisely identify the blocking gap.
