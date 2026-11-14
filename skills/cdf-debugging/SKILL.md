---
name: cdf-debugging
description: Diagnose reproducible defects, failing tests, unexpected behavior or performance regressions using evidence and causal hypotheses before applying a fix. Use for failures; not for ordinary new-feature coding.
---
# Root-cause debugging

1. Record exact symptom, expected behavior, environment, inputs, recent changes and reproducibility. Separate a broken product from a broken test or missing dependency.
2. Reproduce with the smallest faithful path when possible; obtain raw errors, traces and current check output. Do not claim reproduction where unavailable.
3. Trace the first divergence between failing and working paths. List plausible causes; rank by evidence and choose a discriminating experiment instead of speculative edits.
4. Identify root cause or the narrowest remaining uncertainty. Before repair, check whether any material choice about user-facing behavior must go to `cdf-requirements`.
5. When authorized, implement the smallest causal fix. Verify original symptom, adjacent edge cases and no unintended behavior changes.
6. Count unsuccessful repairs of the same observable outcome across turns, including user reports that it remains wrong despite passing tests; distinguish new requirements. After the first rejection, reconcile the observation with prior evidence. After two unsuccessful repairs, run a different discriminating experiment or obtain independent diagnosis before another dependent edit. Keep symptom, attempts, failed hypotheses, accepted constraints and next experiment in context; write a file only for continuity. Continue useful independent work; a subagent is not required.

Record the active revision, route, configuration and relevant data when they could explain source/runtime disagreement. Before each discriminating experiment, predict the different observations for competing hypotheses; update the hypothesis from the result. A passing unit assertion does not by itself resolve the original user complaint.

## Reference
- `references/diagnostic-experiments.md` for multiple competing hypotheses or nondeterministic behavior.

## Optional subskills
Resolve candidates through the bundled catalog only when needed. A portable plugin keeps it at `skills/cdf/subskills.catalog.json`; the legacy installer places it at `.codex/cdf/subskills.catalog.json`. Confirm native discovery and use the local fallback when absent; never install automatically.

- `superpowers-systematic-debugging`: non-obvious root causes, repeated failed fixes, concurrency or multi-component failures.
- `wsh-parallel-debugging`: multiple independent hypotheses where parallel exploration can actually shorten investigation and delegation is available.
Fallback: reproduce → localize → falsify → repair → verify. No random fixes.
