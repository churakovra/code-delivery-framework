# Architecture and contribution guide

CDF is instruction-led. Skills supply focused methods, logical roles supply responsibility, and Codex owns active models, threads, tools and permissions. CDF does not add an agent engine.

`skills/cdf/` and `skills/cdf-*/` are the canonical skill source. `cdf_registry.py` defines 11 core skills and three optional skills. The on-demand kernel owns authority, adaptive delivery and coordination. Requirements owns material decisions and readiness; architecture owns solution proposals and self-critique before dependent implementation; research owns tracing/reuse; debugging owns causal experiments; domain skills own their techniques; verification owns observed checks; review owns independent findings.

The root owns user communication, accepted decisions, integration and completion. Native worker/explorer are conditional execution choices. Two custom templates add review and diagnosis without model pins. Required independent review needs a separate actor. Runtime sandbox controls remain authoritative.

Codex's native plugin manager is the only CDF installation path. `scripts/package_cdf_plugin.py` builds a plugin package but does not install it; the user registers the local marketplace and adds the plugin through Codex. `scripts/cdf.py` provides source validation, optional native-role setup, and desktop-hook diagnostics. It has no plugin or skill installation command.

`CORE` selects the source skills. Native plugin packages keep each skill independently discoverable and include the catalog under `skills/cdf/`. The kernel and specialists retain their source frontmatter, references and presentation metadata. Optional learning skills add two entries; operator adds explicit model calibration. Frozen legacy inventories and fixtures remain historical evidence, not installable skills. The kernel references document current authority, workflow, quality and delegation methods.

`cdf_runtime/contracts.py` validates the bundled schema vocabulary and task invariants. `cdf_runtime/policy.py` resolves advisory candidates and renders explicit native profile proposals. Neither launches agents. Schemas live under `schemas/`; executable examples live under `templates/examples/`.

`evals/` owns fixtures, the controlled runner and result normalization. Historical `CDF_20` retains frozen guidance and rubrics. New comparisons separate `BASE`, an explicitly supplied frozen `LEGACY_CDF_11` snapshot, and `CANDIDATE_CDF`. Match fixtures, runtime settings, tools and permissions; attest provenance and preserve raw evidence. Candidate activation expectations live separately from historical cases. Static assertions or a fixture check cannot prove skill selection, independent review or allowance savings. See the [evaluation protocol](../evals/README.md) for execution prerequisites and limits.

For contributions, identify the owning contract, inspect source, callers and tests, add only useful task-specific guidance, and verify positive and negative scenarios. Run the commands in the repository README. Use disposable targets for native-role setup. Record inspected revisions, licenses and reused content in `sources.json` and `THIRD_PARTY_NOTICES`. Never mark unavailable evidence passed.

`scripts/package_cdf_plugin.py` creates a portable multi-skill plugin from source skills and `templates/cdf-plugin.json`. The optional desktop-controlled profile adds metadata hooks. Packages exclude managed policy blocks and native agent configuration and refuse existing outputs. Packaging has no model-quality claim or registration side effect.

Native role setup is optional configuration over standard Codex TOMLs.
`cdf_installer/agents.py` uses a small receipt for created-role ownership and
transaction helpers. It does not install CDF skills or policy blocks.
`cdf_runtime/codex.py` shares bounded read-only RPC handling between discovery
and catalog checks. Catalog support, configured files and observed execution
remain distinct. Profile rollback removes owned setup rather than retaining a
history of successful profiles. See [installation](installation.md) for setup
and trust boundaries.

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

See [installation and removal](installation.md) for supported setup and removal.
Skills, profiles and hooks are guidance and optional native integration, not an
enforcement engine.
