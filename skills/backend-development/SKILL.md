---
name: backend-development
description: Implement server-side APIs, persistence, and integrations. Not for frontend-only changes.
---

## Scope
Backend implementation within assigned files.
## Context and competencies
Trace the entry point through validation, authorization, domain operations, persistence, response, and side effects. Identify invariants and ownership at each boundary; inspect callers and existing contracts. Validate untrusted values at the boundary that owns them, then rely on established internal types and guarantees. Persisted data, external responses, or process boundaries may introduce a new trust boundary even when internal callers are typed. Consider idempotency, retry behavior, crash recovery, and shared mutable state when the operation or persistence lifecycle makes them relevant. Follow existing architecture and dependency directions.

For lifecycle changes, trace creation, updates, retries, cancellation, failures, and cleanup. Make atomicity and side effects explicit; assess duplicate requests, partial failure and concurrency where applicable. Preserve compatibility or define the migration from the agreed contract.
## Objective
Meet the specified API and data invariants with focused regression coverage.
## Edit permissions
Keep changes within assigned backend ownership; coordinate shared contracts before changing them. External writes require user authorization.
## Evidence
Run project-authoritative checks at the affected unit, integration, or compatibility layer; include integration evidence when persistence or external contracts change. Do not introduce new trust boundaries or dependencies without addressing their guarantees.
## Stopping
Identify unresolved contract behavior before changing it.
