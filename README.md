# Code Delivery Framework

CDF 1.0.0 provides focused delivery skills for Codex. The root agent resolves material requirements, reuses project code, works directly by default, and delegates bounded work when independent review or another concrete benefit warrants it.

## Installation

Use Python 3.11 or newer on a POSIX system. From this checkout:

```sh
python3 scripts/cdf.py validate --offline --json
python3 scripts/cdf.py install --target /path/to/project --dry-run --json
python3 scripts/cdf.py install --target /path/to/project --json
python3 scripts/cdf.py status --target /path/to/project --json
```

Installation makes no network or model calls. It installs 12 core `cdf-*` skills, their references, two native agent templates, an optional-subskill catalog, and one managed AGENTS block. `--with-learning` adds explain and teach; `--with-operator` adds explicit model calibration. See the [bundle inventory](docs/bundle-inventory.md).

Global installation uses `--scope global` with the intended home as `--target`. `--home` selects an explicit alternative home for isolated testing; it must match the target. Project scope manages `<target>/AGENTS.md`; global scope manages `<home>/.codex/AGENTS.md`. Development and tests use temporary targets, never the developer's live configuration.

## Lifecycle

```sh
python3 scripts/cdf.py upgrade --target /path/to/project --dry-run --json
python3 scripts/cdf.py recover --target /path/to/project --dry-run --json
python3 scripts/cdf.py uninstall --target /path/to/project --dry-run --json
python3 scripts/cdf.py doctor --target /path/to/project --json
```

Inspect previews before omitting `--dry-run`. Upgrade retains extras unless explicitly disabled with `--without-learning` or `--without-operator`. Edited managed files block upgrades and are preserved on uninstall. `uninstall --release-modified-skills` preserves each modified skill and releases ownership. The installer preserves bytes outside its AGENTS block, unrelated configuration, and directories containing user files.

Private manifests, backups, transaction journals and cleanup intents are excluded by an additive managed block in `.codex/.gitignore`. That ignore policy persists after uninstall and recovery. Interrupted operations require recovery. Stale locks require manual inspection before removal. The installer does not untrack existing files or change the Git index; inspect already tracked sensitive files separately.

`status` reports recorded file state. Restart Codex and verify discovery in a trusted session to establish active skill and agent availability. `doctor` probes executable availability and version; it does not prove agent behavior.

## Optional tools and model policy

[subskills.catalog.json](subskills.catalog.json) lists optional research candidates, triggers, provenance and local fallbacks. It does not load or install them. `integrations list` and `integrations plan codebase-memory-mcp` are informational. Verify source, license and runtime compatibility before separate installation.

[policies/model-routing.example.toml](policies/model-routing.example.toml) is advisory. It records candidate model/effort pairs, worker budgets and fallback rules; it cannot change a running agent's configuration. Native worker/explorer remain runtime choices; the custom reviewer and diagnostician templates contain no model pins.

## Verification and development

```sh
python3 scripts/validate_cdf.py
python3 scripts/cdf.py validate --offline --json
python3 -m unittest discover -s tests
```

See the [architecture guide](docs/architecture.md), [current acceptance limits](docs/status.md), and [evaluation protocol](evals/README.md). Static checks and fake adapters test mechanics, not model compliance. Live evaluations require explicit execution flags and trusted code. No verified OS sandbox provider, live behavioral acceptance, or subscription savings measurement is claimed.

Release, publishing and deployment require separate authorization. [sources.json](sources.json) and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES) preserve research provenance and licensing information.
