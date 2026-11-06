# Backend architecture decision guide

**Start with the repository's existing ownership and dependency direction.** Trace the current feature path and at least one adjacent implementation before proposing new architecture. A directory called `domain` does not itself establish clean architecture; constraints and dependencies do.

## Choosing a structure
- **Simple handler/module**: one behavior, limited dependencies, no meaningful domain boundary; keep it straightforward.
- **Application service / use case**: the same orchestration is reused or coordinates multiple side effects with nontrivial error semantics; keep transport specifics at the edges.
- **Domain model or value object**: central invariants must survive across endpoints, jobs and adapters; put rules where they cannot be bypassed.
- **Port / adapter abstraction**: external implementation is variable or testing needs a controlled boundary. Do not create empty one-to-one interfaces for every class.
- **Repository abstraction**: a real data access contract is reused, must isolate backend-specific persistence, or protects complex transactional semantics. A single query does not mandate a repository.

## Dependency checks
Trace import direction, lifecycle and ownership. Avoid cyclic imports, framework annotations in stable domain types when they create coupling, and service layers that merely forward arguments. Data validation belongs to trust boundaries; deeper invariants belong where all paths enforce them. Do not duplicate the same invariant in five validators.

## Decision test
What specific failure, duplication, change pressure or test friction does this abstraction prevent? Which simpler option did you reject, and why? If the answer is speculative, keep the simpler design. Do not perform adjacent refactoring without a requirement or concrete risk.

## Source inspirations
`wsh-architecture` (optional) and CDF source history. Links and license metadata live in `subskills.catalog.json`.
