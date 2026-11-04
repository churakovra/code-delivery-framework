---
name: implementation
description: Implement an authorized, bounded repository change using project conventions. Use for general code or configuration work.
---

## Scope
Own assigned production code and related focused tests.
## Context and competencies
Inspect instructions, callers, tests, patterns, and the dirty baseline. Prefer the smallest change that meets the agreed behavior. Add abstraction, configuration, defensive handling, or tests for concrete needs, not hypothetical ones. Preserve public compatibility, state integrity, cleanup, and observability where relevant.
## Objective
Satisfy observable requirements; inspect the complete diff and failure paths.
## Edit permissions
Edit assigned files only; coordinate ownership and preserve others’ edits. Do not commit, publish, merge, or deploy without explicit authorization.
## Evidence
Add or update a behavioral regression check when it can capture the reported outcome; reproduce a failing test first when practical, without forcing a TDD cycle when the test is impractical. Run relevant project checks and report exact commands/results. Do not run broad suites solely for docs or copy changes.
