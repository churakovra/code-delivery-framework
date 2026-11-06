# Choosing the cheapest credible verification

| Changed behavior | Primary evidence | Escalation |
|---|---|---|
| Pure function | Focused unit assertions including edge case | Property-based checks for complex invariants |
| HTTP/API contract | Request/response integration or contract test | Compatibility suite if public interface changes |
| DB transaction/migration | Real DB integration and integrity checks | Upgrade/rollback rehearsal if consequential |
| Async/event processing | Deterministic duplicate, cancellation, timeout or partial-failure test | Controlled integration across queue/DB boundary |
| UI interaction | Real component interaction + type/build checks | Browser keyboard/visual check for significant UX |
| Documentation-only | Link/path/command checks as relevant | Do not run unrelated application suites |

Tests should fail for the bug being addressed, not just assert current implementation details. Prefer existing fixtures and production paths. Do not impose a full new testing framework to cover a tiny change. A passing mocked test does not prove behavior at an unmocked boundary. Report the checked revision, commands, exit codes and skipped/unavailable tests.
