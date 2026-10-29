---
name: implementation
description: Implement an authorized, bounded repository change using project conventions. Use for general code or configuration work.
---

## Scope
Own assigned production code and related focused tests.
## Context and competencies
Read applicable instructions, callers, tests, and nearby established patterns. Capture the dirty baseline. Prefer the smallest coherent edit; add an abstraction when reuse, composition, or a clear boundary benefits from it. Preserve public compatibility, state integrity, cleanup, and observability where relevant.
## Objective
Make the smallest coherent change that satisfies observable requirements, then inspect the complete diff and failure paths.
## Edit permissions
Edit assigned files only; coordinate ownership and preserve others’ edits. Do not commit, publish, merge, or deploy without explicit authorization.
## Evidence
Add or update a behavioral regression check when it can capture the reported outcome; reproduce a failing test first when practical, without forcing a TDD cycle when the test is impractical. Run relevant project checks and report exact commands/results. Do not run broad suites solely for docs or copy changes.
## Stopping
After two failed repair cycles on the same acceptance failure, stop and request independent diagnosis.

## Conditional helpers
- Read `../helpers/regression-testing.md` only for: A behavior change or repair with a meaningful observable regression.
- Read `../helpers/diagnosis.md` only for: A reproducible bug, failed check, or unexpected behavior.
- Read `../helpers/react.md` only for: React or Next.js code with relevant rendering, fetching, or performance concerns.
- Read `../helpers/accessibility.md` only for: Changed interactive UI or an explicitly requested accessibility review.
