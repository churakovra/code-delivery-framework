# Hypothesis-driven diagnosis

Start a tiny ledger when failure is not locally obvious:

| Observation | Hypothesis | Differentiating experiment | Predicted result | Actual result |
|---|---|---|---|---|

Try to identify the *first* divergence from the expected behavior, not the last logged exception. Reproduce with stable inputs and the same relevant environment, then vary one causal factor at a time. For concurrency and intermittent problems, record timing, idempotency keys, process boundaries and reproducibility limits without forcing unreliable delays.

Compare affected and unaffected code paths, old and new revisions, and versions of the contract. Log only what is needed; avoid dumping credentials or user payloads.

If an experiment fails to support a hypothesis, update it rather than stacking speculative patches. Two failed repair attempts with the same premise require a different causal analysis before further editing. A parallel specialist is justified only if independent hypotheses can be investigated without conflicting writes.

A fix is not validated until the original symptom and a relevant regression path are checked on the revised source. Environmental blockers are reported distinctly.
