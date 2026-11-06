# Async Python, concurrency and failure lifecycle

1. Identify blocking operations. `async def` around synchronous I/O does not create concurrency. Use asynchronous libraries or offload blocking calls only where appropriate.
2. Each spawned task needs an owner, cancellation policy and awaited/joined lifecycle. Prefer scoped concurrency (e.g., `TaskGroup` when supported by the project Python version); fire-and-forget is only safe with explicit tracking/error reporting.
3. Treat cancellation as control flow; close network, DB and file resources even after timeout or cancellation. Do not broadly swallow `CancelledError`.
4. Deadlines must cover the complete operation. Multiple nested timeouts and retries can multiply latency; bound total attempts and apply jitter only when the remote service and business operation warrant it.
5. Define whether operations are safe to retry, deduplicated, or compensatable. Exactly-once execution is not obtained merely by adding a queue.
6. For shared state, decide lock granularity and data ownership; check races across processes/transactions, not just asyncio tasks.
7. Test cancellation, timeout, duplicated delivery and partial failure only when relevant to the changed path. Use a controlled schedule/clock where practical instead of flaky sleeps.
