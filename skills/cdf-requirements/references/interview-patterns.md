# Requirements interview decision patterns

**Trigger examples:** 'make auth more secure' (undefined policy), 'improve errors' (undefined user behavior), 'let the job run in background' (ambiguous completion semantics), 'rename the local helper for consistency' (routine, no interview).

## Material decisions
Ask what determines accepted behavior. For each currently answerable question, provide:
- observed fact and reason decision matters;
- options and tradeoffs;
- recommended option explicitly marked *unapproved*;
- requested user choice.

Ask independent questions together; do not ask downstream questions before upstream answers make them meaningful. Do not ask for technical trivia that the implementer can safely decide. Confirm only consequential decisions, not every implementation detail.

## Compact readiness record
```yaml
goal: <observable outcome>
confirmed: [<user decisions with source/turn>]
constraints: [<real technical and business limits>]
acceptance: [<observable tests/behaviors>]
blocking: [<unresolved consequential choices>]
status: READY | BLOCKED | EXPLORATORY
```

Never silently convert a recommendation into approval. Reuse answers already in context or project docs. If the user explicitly delegates a business decision, document that delegation and its boundaries.

Ask the independent frontier only after code and prior answers establish prerequisites. State gap, consequence, alternatives and an unapproved recommendation. Record the decision source/scope; reconcile affected acceptance after a user or revision change.
