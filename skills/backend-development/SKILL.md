---
name: backend-development
description: Implement or revise server-side behavior, APIs, persistence, and integrations. Use when backend contracts or data flows are in scope.
---

## Scope
Backend implementation within assigned files.
## Context and competencies
Trace request/data flow, callers, persistence boundaries, authorization, transactions, and failure handling. Validate untrusted values at the boundary that owns them, then rely on established internal types and guarantees. Persisted data, external responses, or process boundaries may introduce a new trust boundary even when internal callers are typed. Consider idempotency, retry behavior, crash recovery, and shared mutable state when the operation or persistence lifecycle makes them relevant. Follow existing architecture and dependency directions.
## Objective
Meet the specified API and data invariants with focused regression coverage.
## Edit permissions
Keep changes within assigned backend ownership; coordinate shared contracts before changing them. External writes require user authorization.
## Evidence
Run project-authoritative checks at the affected unit, integration, or compatibility layer; include integration evidence when persistence or external contracts change. Do not introduce new trust boundaries or dependencies without addressing their guarantees.
## Stopping
Do not guess at ambiguous contract behavior. Stop after two failed repair cycles and seek independent diagnosis.
