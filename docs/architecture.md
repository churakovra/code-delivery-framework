# CDF 2.0 architecture and contribution guide

CDF is instruction-led. Skills supply focused methods, logical roles supply responsibility, and Codex owns active models, threads, tools and permissions. CDF does not add an agent engine.

`skills/cdf-*/` is the canonical skill source: 12 core, one operator extra, two learning extras. Proposal appendices are historical design text. A primary skill selects a narrow optional catalog entry only for a concrete trigger; registry presence never proves installation.

`templates/AGENTS.cdf-block.md` supplies minimal consumer policy. Requirements owns material decisions/readiness, orchestration owns direct/delegated delivery, implementation/domain skills own methods, verification owns observed checks, and review owns independent findings. Avoid copying all procedures into role profiles. `templates/AGENTS.md` and unprefixed skills remain isolated legacy sources pending release gates.

The root owns user communication, accepted decisions, integration and completion. Native worker/explorer are conditional execution choices. The two custom templates add review/diagnosis without model pins. Required independent review needs a separate actor. Runtime sandbox controls remain authoritative.

The lifecycle is classification/discovery, readiness, optional planning, implementation, verification and risk-triggered review. Material questions block dependent edits; routine choices stay with the engineer. Checkpoint/handoff JSON is optional for continuity and evaluation. `cdf_runtime/contracts.py` validates the bundled schema vocabulary and task invariants; `cdf_runtime/policy.py` resolves advisory candidates. Neither launches agents.

`scripts/cdf.py` is the v2 CLI. Its installer builds a desired map, checks paths and ownership, and applies a journaled transaction with the manifest last. `.codex/cdf/manifest.json` records hashes, extras, managed blocks and preimages. Preserve outside AGENTS bytes, local edits and unrelated configuration. Core commands never download binaries or call a task model. Migration from 0.6 is report-only, followed by removal with the old version's uninstaller.

`evals/` owns fixtures, controlled runner and result normalization. Compare matching fixtures and runtime settings across BASE, pinned CDF_06 and CDF_20. Preserve raw evidence. Static assertions or a fixture check cannot prove skill selection, independent review or allowance savings.

For contributions, identify the owning contract, inspect source/callers/tests, add only useful task-specific guidance, and verify positive and negative scenarios. Run `python3 -m unittest discover -s tests` and `python3 scripts/validate_cdf.py`. Installer tests use temporary targets. Record actual revisions, licensing and reused content in `sources.json` and `THIRD_PARTY_NOTICES`. Follow the [acceptance matrix](plans/cdf-2.0/tests/ACCEPTANCE-MATRIX.md) and [implementation status](plans/cdf-2.0/IMPLEMENTATION_STATUS.md); never mark unavailable evidence passed.
