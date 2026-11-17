---
name: cdf-testing
description: Design, write, refactor or remove tests around meaningful behavioral guarantees and credible failure boundaries. Use for regression design, test quality, consolidation, idempotency or concurrency tests; not running existing checks, trivial edits without protected logic, or coverage targets alone.
---
# Meaningful tests

1. For each substantial test identify the behavior/invariant, plausible defect that would fail it, cheapest credible observation boundary, unique signal and fixture/runtime/diagnostic cost. Keep this in context; no test passport is required. Redesign or omit tests without meaningful regression signal unless they serve a necessary infrastructure check.
2. Match the boundary to the claim. Pure rules and domain transformations usually need focused units, not Docker or browsers. HTTP/auth needs the real request/ASGI path with realistic dependencies; isolate external I/O where appropriate. PostgreSQL uniqueness and transactions need a real database, not repository mocks. Event retries need durable state, claim/recovery, retry timing and network adapter boundaries. A mocked provider transport establishes the local client contract, not live provider behavior. UI journeys need real interaction where applicable. Do not replace all unit tests with integration tests.
3. Before substantive test consolidation or deletion, make a compact Test Guarantee Ledger of unique protected invariants: KEEP (independent guarantee), REWORK (needed behavior, wrong boundary), MERGE (move guarantee), REMOVE (no useful signal or fully covered). Afterward map every retained unique guarantee to its new test. Preserve distinctions such as replay/null equivalence and final-attempt conflict handling; count and coverage cannot prove preservation. No persistent ledger file is required.
4. For critical, ambiguous or broadly rewritten tests, spot-check that a plausible defect is caught using a bounded mutation or regression red/green. Record the observed failure and repair. Restore every temporary mutation; never leave a bug or disabled check. A full mutation framework is optional.
5. Reuse production paths and existing fixtures. Avoid tests that merely assert mock calls or mirror implementation while claiming an unexercised boundary. Explain unavailable integration evidence; do not invent results. Ordinary useful unit tests remain valid and cheap.

Pass the intended guarantee, checked boundary and remaining gaps to cdf-verification for fresh commands/results. cdf-code-review assesses guarantee preservation and solution fit. A trivial documentation edit needs no new test.

## Optional subskills
Resolve candidates through the bundled catalog only when needed. The Codex plugin keeps it at `skills/cdf/subskills.catalog.json`. Confirm native discovery and compatibility; never install automatically.

- `wsh-python-testing`: Python/pytest fixture, isolation or async test design.
- `superpowers-tdd`: a consequential regression suited to observed red/green.
Fallback: direct behavior/failure/boundary analysis, a compact in-context ledger when needed, and focused regression checks using the project's tools.
