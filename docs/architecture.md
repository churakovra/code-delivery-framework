# Architecture and contribution guide

CDF is instruction-led. Skills supply focused methods, logical roles supply responsibility, and Codex owns active models, threads, tools and permissions. CDF does not add an agent engine.

`skills/cdf/` and `skills/cdf-*/` are the canonical skill source. `cdf_registry.py` defines 11 core skills and three optional skills. `templates/AGENTS.cdf-block.md` supplies short always-on consumer policy. The on-demand kernel owns authority, adaptive delivery and coordination. Requirements owns material decisions and readiness; architecture owns solution proposals and self-critique before dependent implementation; research owns tracing/reuse; debugging owns causal experiments; domain skills own their techniques; verification owns observed checks; review owns independent findings.

The root owns user communication, accepted decisions, integration and completion. Native worker/explorer are conditional execution choices. Two custom templates add review and diagnosis without model pins. Required independent review needs a separate actor. Runtime sandbox controls remain authoritative.

`scripts/cdf.py` is the CLI. `cdf_installer/core.py` builds a desired map, checks paths and ownership, and applies a journaled transaction with the manifest last. `.codex/cdf/manifest.json` records hashes, extras, managed blocks and preimages. Preserve bytes outside AGENTS blocks, local edits and unrelated configuration. Core commands never download binaries or call a task model.

`CORE` selects source modules. `[tool.cdf].layout = "single"` in the source `pyproject.toml` makes new installations expose only `cdf/SKILL.md`; undeclared layout denotes historical flat bundles. `cdf_installer/packaging.py` maps specialists to `cdf/modules/<name>/GUIDE.md`, preserves relative references, creates a trigger index, and omits specialist UI metadata. The source methods remain independently maintained; only the kernel has native picker metadata and icons. Specialist guides have no standalone presentation assets. Model calibration stays explicitly requested. Frozen `LEGACY_CORE_11` recognizes historical ownership. Installed manifests must match the declared layout: one CDF entry plus all selected module guides, or one known historical flat inventory plus its declared extras. Schema-2 manifests now carry an optional `layout` field; absence means flat. Older installers reject this new field, so use the current installer for single-layout status, recovery and removal. Partial manifests may retain a subset of one generation. Recovery and empty-directory cleanup accept known historical paths without allowing arbitrary skill names. The schema remains version 2, and version downgrade refusal still applies. Migration tests cover original 1.1.0 installations produced from pinned repository source by its own installer, plus adversarial synthetic fixtures. The current source upgrades both project and global targets; crash recovery, conflicts and downgrade refusal remain tested. The kernel references document the current authority, workflow, quality and delegation methods.

`cdf_runtime/contracts.py` validates the bundled schema vocabulary and task invariants. `cdf_runtime/policy.py` resolves advisory candidates and renders explicit native profile proposals. Neither launches agents. Schemas live under `schemas/`; executable examples live under `templates/examples/`.

`evals/` owns fixtures, the controlled runner and result normalization. Historical `CDF_20` retains frozen guidance and rubrics. New comparisons separate `BASE`, an explicitly supplied frozen `LEGACY_CDF_11` snapshot, and `CANDIDATE_CDF`. Match fixtures, runtime settings, tools and permissions; attest provenance and preserve raw evidence. Candidate activation expectations live separately from historical cases. Static assertions or a fixture check cannot prove skill selection, independent review or allowance savings. See the [evaluation protocol](../evals/README.md) for execution prerequisites and limits.

For contributions, identify the owning contract, inspect source, callers and tests, add only useful task-specific guidance, and verify positive and negative scenarios. Run the commands in the repository README. Installer tests use temporary targets. Record inspected revisions, licenses and reused content in `sources.json` and `THIRD_PARTY_NOTICES`. Never mark unavailable evidence passed.

`scripts/package_cdf_plugin.py` creates a portable multi-skill plugin from standalone source skills and `templates/cdf-plugin.json`; the legacy installer keeps its compact layout. It includes the catalog under `skills/cdf/` but excludes private installer state, policy blocks, and native agent configuration. It refuses existing outputs. Plugin packaging has no model-quality claim and no registration side effect.

Native profile setup is a separate optional installer path over standard Codex
TOMLs. `cdf_installer/agents.py` reuses the existing lock/transaction/recovery,
with a small receipt for created-role ownership; it does not install a legacy
skill or AGENTS block. `cdf_runtime/codex.py` shares bounded read-only RPC handling
between discovery and catalog checks. Catalog support, configured files and
observed execution remain distinct. Profile rollback removes owned setup rather
than retaining a history of successful profiles. See [installation](installation.md) for lifecycle and trust boundaries.

The experimental desktop build adds one standalone metadata observer under
`hooks/`. It uses native hook discovery/trust, not an alternative event engine.
`cdf_runtime/hooks.py` reads native `hooks/list` and optionally an explicitly
selected bounded log; it never scans session transcripts or grants trust.
History is not current enforcement evidence. The desktop compatibility manifest
is selected by an explicit build profile; portable output remains unchanged.
Runtime behavior and overhead must be checked on the intended host; discovery
is not execution proof.

SessionStart reads only bounded known CDF manifest/receipt metadata and returns a
compact version/profile/mode context. Role-file detection is not availability or
routing; no user source or session transcript is read. PostToolUse, PreToolUse
and Stop remain omitted by the accepted necessity decision. There is no hook
engine, automatic trust, semantic command parser or enforcement claim.

See [installation, migration and removal](installation.md) for supported setup,
recovery and disable/remove operations. Skills, profiles and hooks are guidance
and optional native integration, not an enforcement engine.
