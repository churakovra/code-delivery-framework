# Adaptive delivery

Distinguish explain/explore/audit/plan from implement/operate. Read-only work and a plan do not authorize code changes. Implementation does not authorize publication or global configuration changes.

- SIMPLE: a known local, low-risk change → inspect the relevant context, edit, focused check, diff inspection. No mandatory plan, question, child or full suite.
- STANDARD: connected modules or meaningful uncertainty → compact acceptance in context, reversible increments ordered by dependencies, relevant contract/integration checks and risk-based review.
- COMPLEX: authorization, sensitive data, migrations, concurrency or difficult rollback → explicit invariants and alternatives, resolve material choices, validate adverse paths and obtain independent review.

Change mode when evidence changes risk. A file count or the word API does not determine complexity. Prefer established helpers and conventions; coordinate shared contracts before parallel edits. A plan records outcome, boundaries, dependencies and acceptance-to-check mapping, not a new runtime.

For continuity retain accepted intent/scope, decision sources, branch/HEAD, evidence freshness, failed attempts, open questions and next step. Keep this in context unless a durable handoff needs a file. Recheck affected facts after revision or scope changes.

User rejection is new outcome evidence even with green tests. After the first rejection reconcile the active path/version/configuration and prior checks. After two failed repairs use a different discriminating experiment or independent diagnosis before another dependent edit; use cdf-debugging for the method. Distinguish a new requirement from an unsuccessful repair.

Before another search, tool, skill, child or test suite identify the uncertainty it closes. Stop when contracts, reuse and acceptance are sufficiently grounded. Expand checks for risk, new changes or failures; do not truncate critical evidence to save tokens or repeat broad checks without a reason.
