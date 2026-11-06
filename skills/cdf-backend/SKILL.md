---
name: cdf-backend
description: Implement or review server APIs, domain/application logic, persistence, async processing, messaging and external integrations. Use on backend changes; do not load for frontend-only or documentation-only work.
---
# Backend engineering

1. Trace a request or event from input through authorization/validation, domain decisions, state transition, side effects and response. Mark trust boundaries and invariants. Inspect existing services, repositories, schemas and tests before introducing alternatives.
2. Select architecture by the existing system and complexity: a direct module is fine for simple behavior; add use cases, ports/adapters or domain types when they isolate real changing dependencies or protect invariants. Do **not** impose Clean Architecture folder layouts without a concrete benefit.
3. Preserve public API contracts: versioned schemas, error semantics, permissions, pagination, idempotency, backwards compatibility and serialization. Raise unspecified external behavior to `cdf-requirements`.
4. For persistence: define transaction boundary, constraints, concurrency and migration/rollback behavior. Never silently lose data; consider duplicate deliveries, retries and partial failures only when the operation has these hazards.
5. For async/concurrency: establish ownership of tasks, cancellation, deadlines, resource cleanup, blocking operations and backpressure. Use retries only for safe/recoverable operations with bounded policies.
6. Reuse established libraries and patterns. Write focused regression evidence; include integration/contract checks for schema, DB or external integration changes. Read only the relevant local reference when deeper decisions arise.

## References on demand
- `references/architecture.md` — dependency direction, ports and abstractions.
- `references/contracts.md` — APIs, persistence, events and compatibility.
- `references/async-and-failures.md` — cancellation, retries, idempotency and recovery.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `wsh-architecture`: genuine new architectural boundary/DDD/hexagonal design.
- `wsh-api-design`: consequential REST/GraphQL interface design.
- `wsh-postgres`: PostgreSQL schema, constraints, indexing or online migration.
- `wsh-async-python`: complex Python async lifecycle.
Fallback: the rules above and project/local references; no dependency merely because backend code exists.
