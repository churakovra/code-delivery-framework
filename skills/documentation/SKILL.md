---
name: documentation
description: Update documentation to reflect current behavior and authoritative project guidance. Use alongside implementation or for documentation-only changes.
---

## Scope
Own assigned documentation files.
## Context and competencies
Read the brief, actual changes, and authoritative topic docs. Preserve important invariants, generated-file rules, project test commands, and operational pitfalls. Replace stale descriptions, link to canonical topics, and mark gaps explicitly. Keep requirements and technical gates intact.
## Objective
Make docs accurate, concise, navigable, and consistent with delivered behavior.
## Edit permissions
Edit only owned docs; preserve unrelated changes.
## Evidence
Inspect content, links, and the complete documentation diff; run relevant static checks. Do not run application suites solely for docs.
## Stopping
Report implementation gaps or unavailable evidence explicitly; do not imply unrun evaluations passed.

## Conditional helpers
- Read `../helpers/communication.md` only for: Ambiguity-sensitive instructions or agent handoffs.
