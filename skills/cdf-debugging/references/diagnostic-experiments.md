# Hypothesis-driven diagnosis

Start a tiny ledger when failure is not locally obvious:

| Observation | Hypothesis | Differentiating experiment | Predicted result | Actual result |
|---|---|---|---|---|

Try to identify the *first* divergence from the expected behavior, not the last logged exception. Reproduce with stable inputs and the same relevant environment, then vary one causal factor at a time. For concurrency and intermittent problems, record timing, idempotency keys, process boundaries and reproducibility limits without forcing unreliable delays.

Compare affected and unaffected code paths, old and new revisions, and versions of the contract. Log only what is needed; avoid dumping credentials or user payloads.

If an experiment fails to support a hypothesis, update it rather than stacking speculative patches. Two failed repair attempts with the same premise require a different causal analysis before further editing. A parallel specialist is justified only if independent hypotheses can be investigated without conflicting writes.

A fix is not validated until the original symptom and a relevant regression path are checked on the revised source. Environmental blockers are reported distinctly.

User feedback is evidence: when the same outcome is rejected again, compare it with the prior prediction even if technical checks passed. Carry failed attempts across turns. Distinguish a changed requirement from a failed repair. For source/runtime disagreement, a useful experiment verifies the active version, configuration and data before changing another parameter. Keep this checkpoint in context unless continuity needs a file.

For each competing cause predict a different observable result before the experiment. Compare active route/version/configuration and real data with the edited source. Preserve failed predictions; do not reinterpret a green unit check as proof of the original outcome.
