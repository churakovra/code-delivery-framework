# APIs, persistence and messaging contracts

**API:** Preserve existing path/method/version, accepted payload shape, authorization, response/error schema and status semantics unless change is approved. Distinguish 400 invalid request, 401 unauthenticated, 403 unauthorized, 404 absent, and 409 conflict only according to existing contract. Beware idempotency and retries: HTTP method names alone do not prove side-effect safety.

**Database:** State domain invariants, transaction boundary and constraints. For concurrent updates, decide whether optimistic version checks, row locks or uniqueness constraints enforce the invariant. Record migration compatibility for old and new application versions, deployment ordering, backfills and rollback limits. Avoid importing test-only behavior into production.

**Events/queues:** Define message ownership, acknowledgement timing, at-most/at-least-once expectations, retryable failures, poison messages, ordering assumptions, consumer idempotency and reconciliation. Outbox/inbox patterns are justified only when crossing a transaction/message boundary could violate a required guarantee.

**External clients:** Define timeouts, response validation, bounded retries and authentication. Do not retry non-idempotent writes blindly. Follow existing logging/metrics style without exposing secrets or personal payloads.

**Checks:** Test observable endpoints and errors, real persistence constraints, relevant migration paths and event semantics. A mocked repository cannot prove database atomicity.
