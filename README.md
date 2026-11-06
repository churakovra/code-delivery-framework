# Code Delivery Framework 2.0 (development)

CDF delivers the behavior agreed with the user through focused skills. The root works directly by default, reuses project code, resolves material requirements before dependent edits, and delegates bounded work when independent review or another concrete benefit warrants it.

This checkout is **2.0.0.dev0**, not a released or benchmark-validated version. See the [implementation plan](docs/plans/cdf-2.0/README.md) and [current evidence and release gates](docs/plans/cdf-2.0/IMPLEMENTATION_STATUS.md). No subscription savings are claimed.

## Offline installation

Use Python 3.11 or newer. From this source checkout:

```sh
python3 scripts/cdf.py validate --offline --json
python3 scripts/cdf.py install --target /path/to/project --dry-run --json
python3 scripts/cdf.py install --target /path/to/project --json
python3 scripts/cdf.py status --target /path/to/project --json
python3 scripts/cdf.py doctor --target /path/to/project --json
```

Core installation makes no network or model calls. It installs **12 `cdf-*` skills**, their references, **two native agent profiles**, an optional-subskill catalog, and one managed AGENTS block. It never changes `.codex/config.toml`, Git branches/index, MCP binaries or community skills. Develop and test only in disposable targets.

`--with-learning` adds explain and teach; `--with-operator` adds explicit model calibration. Together all extras give 15 skills. Upgrade retains extras unless `--without-learning` or `--without-operator` removes them. Calibration has explicit-only invocation metadata.

For global use, select the intended home as target and use `--scope global`; `--home /path/to/temporary-home` explicitly selects a different home for isolated testing. Target and selected home must match. Test this mode in a **temporary home**, never the developer's live configuration. Project scope manages `<target>/AGENTS.md`; global scope manages `<home>/.codex/AGENTS.md`. Target paths must be canonical (for example, resolve macOS `/tmp` to `/private/tmp`). Files live under `.agents/skills/cdf-*/`, `.codex/agents/`, and `.codex/cdf/`.

## Lifecycle and migration

```sh
python3 scripts/cdf.py upgrade --target /path/to/project --dry-run --json
python3 scripts/cdf.py recover --target /path/to/project --dry-run --json
python3 scripts/cdf.py uninstall --target /path/to/project --dry-run --json
python3 scripts/cdf.py migrate-legacy --target /path/to/project --dry-run --json
```

Inspect each preview, then omit `--dry-run` to apply. `migrate-legacy` is **report-only** and always requires `--dry-run`. A normal upgrade refuses 0.6 installations. Follow the [manual migration procedure](docs/plans/cdf-2.0/docs/05-installer-and-distribution.md#59-legacy-v06-migration-behavior-explicitly-manual-for-v200): inspect/recover the old installation, make a private backup, use its own uninstaller, resolve leftovers, then preview v2. Restore preferences, not obsolete generated agents.

Edited managed files block upgrades and are preserved on uninstall. Unrelated AGENTS bytes are preserved. Interrupted changes use a preimage journal; recovery preserves files changed after the transaction for reconciliation. A stale lock is never silently stolen: confirm no operation is running before removing it. New manifests record directories created by CDF; uninstall removes those only while empty, preserving pre-existing and user-populated directories. A managed additive block in `.codex/.gitignore` excludes CDF private state without changing the repository-root ignore file. Cleanup intent lives at `.codex/cdf-cleanup.json`; legacy root `.cdf-cleanup.json` intents remain recoverable. Older manifests without directory ownership records are preserved conservatively; a crash before a directory creation is journaled can leave an empty directory. Uninstall may be repeated after paths disappear. Modified skills remain preserved and block full ownership removal unless `--release-modified-skills` is selected; that option preserves the whole modified skill and releases CDF ownership. AGENTS content and its backup remain preserved. CDF never untracks existing files or rewrites the Git index; inspect and remediate tracked secrets manually.

`status` describes recorded bytes, not active behavior. Unavailable discovery or agent evidence remains `unverified`. Start a fresh trusted Codex session and check skill/agent discovery. Current [discovery evidence](docs/plans/cdf-2.0/discovery-evidence.json) covers 12 core skill names in one isolated runtime; it does not prove task behavior or every platform.

JSON output is one object per invocation. Exit codes: 0 success, 2 invalid request/conflict, 3 recovery required, 4 strict runtime validation unavailable, 5 filesystem/system error. See the [CLI contract](docs/plans/cdf-2.0/docs/09-implementation-interfaces.md).

## Skills, agents and models

The core covers requirements, planning, codebase research, implementation, backend, frontend, UI design, debugging, verification, review, documentation and orchestration. Read only relevant skills. Codebase Memory is optional, with source-search fallback.

Roles describe responsibility. Native worker/explorer cover delegated implementation and research. Custom `cdf_reviewer` and `cdf_diagnostician` templates have no model pins. Read-only instructions do not create a sandbox. High-risk changes need independent review; missing mandatory review blocks readiness. Medium-risk review depends on changed contracts, failure evidence and rollback confidence. Existing project requirements still apply.

[model-routing.example.toml](policies/model-routing.example.toml) is advisory, not Codex configuration. `cdf_runtime/policy.py` records candidates, requests, observations and fallback; it neither launches agents nor switches the root model. The orchestration skill applies an explicitly selected operator profile, including its worker budget, medium-risk review preference and supported fallback rules. Without a selected policy, it keeps the current session settings and a two-worker default. `python3 scripts/inspect_cdf_policy.py --policy policies/model-routing.example.toml --risk HIGH` reports deterministic advisory decisions without launching agents. Proposed model/effort pairs require actual runtime validation. API prices and instruction sizes are not Plus allowance measurements.

`subskills.catalog.json` contains **31 optional candidates**, activation rules, reported revisions, license caveats and local fallbacks. It is metadata, not a loader. `integrations list` and `integrations plan codebase-memory-mcp` print informational plans only. Sources inherited from the proposal are labeled in `sources.json`; verify exact upstream assets before separate installation. No external skills are vendored.

## Verification

```sh
python3 -m unittest discover -s tests
python3 scripts/validate_cdf.py
python3 scripts/cdf.py validate --offline --json
```

Tests use temporary targets. Static checks do not prove model compliance. The [evaluation runner](evals/README.md) compares BASE, pinned CDF 0.6, and CDF 2.0 in isolated homes/workspaces. Behavioral comparisons score the same task criteria across conditions; CDF2 skill activation is reported separately and remains a release-readiness requirement. Versioned rubrics reject incompatible earlier artifacts. Fake adapters test harness mechanics only. Live evaluations require `--allow-model-runs` and `--trusted-local-execution`, a supported authenticated adapter and a bounded run budget. The latter is a trust decision, not isolation; no verified OS sandbox provider is shipped. The runner is POSIX-only and preflight does not execute an adapter or verify Codex version/resume compatibility. Unknown activation, review, model or usage evidence stays unobserved.

CI is configured for Ubuntu and macOS with Python 3.11/3.13 and Node 22, running model-free checks. This workflow has not been remotely executed and branch protection is not configured. `scripts/validate_cdf.py --write-inventory` regenerates `docs/bundle-inventory.md`; normal validation checks that generated inventory for freshness.

Legacy installer sources and tests remain for rollback and historical controls until release gates permit pruning. Their payload excludes new `cdf-*` skills. Use the pinned 0.6 checkout for legacy operations; [historical documentation](docs/legacy/README-0.6.md) remains for reference. Publishing, live migration and release are separate authorized actions.

See [architecture](docs/architecture.md), [sources](sources.json) and [third-party notices](THIRD_PARTY_NOTICES).
