# Architecture and contribution guide

CDF is instruction-led. Skills supply focused methods, logical roles supply responsibility, and Codex owns active models, threads, tools and permissions. CDF does not add an agent engine.

`skills/cdf-*/` is the canonical skill source. `cdf_registry.py` defines 12 core skills and three optional skills. `templates/AGENTS.cdf-block.md` supplies consumer policy. Requirements owns material decisions and readiness; orchestration owns direct or delegated delivery; implementation and domain skills own methods; verification owns observed checks; review owns independent findings.

The root owns user communication, accepted decisions, integration and completion. Native worker/explorer are conditional execution choices. Two custom templates add review and diagnosis without model pins. Required independent review needs a separate actor. Runtime sandbox controls remain authoritative.

`scripts/cdf.py` is the CLI. `cdf_installer/core.py` builds a desired map, checks paths and ownership, and applies a journaled transaction with the manifest last. `.codex/cdf/manifest.json` records hashes, extras, managed blocks and preimages. Preserve bytes outside AGENTS blocks, local edits and unrelated configuration. Core commands never download binaries or call a task model.

`cdf_runtime/contracts.py` validates the bundled schema vocabulary and task invariants. `cdf_runtime/policy.py` resolves advisory candidates. Neither launches agents. Schemas live under `schemas/`; executable examples live under `templates/examples/`.

`evals/` owns fixtures, the controlled runner and result normalization. Compare the bare BASE condition with the installed CDF_20 condition under matching fixtures and attested runtime settings. CDF_20 is the current harness condition identifier, independent of package version. Preserve raw evidence. Static assertions or a fixture check cannot prove skill selection, independent review or allowance savings.

For contributions, identify the owning contract, inspect source, callers and tests, add only useful task-specific guidance, and verify positive and negative scenarios. Run the commands in the repository README. Installer tests use temporary targets. Record inspected revisions, licenses and reused content in `sources.json` and `THIRD_PARTY_NOTICES`. Never mark unavailable evidence passed.
