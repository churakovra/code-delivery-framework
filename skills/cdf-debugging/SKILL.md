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
6. After two unsuccessful repairs of the *same* failure, stop repeating the same premise; propose an independent diagnosis or a different experiment. Escalate without dumping an unbounded transcript.

## Reference
- `references/diagnostic-experiments.md` for multiple competing hypotheses or nondeterministic behavior.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `superpowers-systematic-debugging`: non-obvious root causes, repeated failed fixes, concurrency or multi-component failures.
- `wsh-parallel-debugging`: multiple independent hypotheses where parallel exploration can actually shorten investigation and delegation is available.
Fallback: reproduce → localize → falsify → repair → verify. No random fixes.
