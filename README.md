# Code Delivery Framework

CDF provides focused delivery skills for Codex. The root agent resolves material requirements, reuses project code, works directly by default, and delegates bounded work when independent review or another concrete benefit warrants it. The package version is defined in `[project].version` in `pyproject.toml`.

Ask naturally, for example: “Add order export using the existing access rules.” The agent inspects the current path, asks about material decisions the code and prior answers do not settle, implements a bounded change, and reports observed checks and gaps. The managed policy supplies short always-on safeguards; the `cdf` kernel handles nontrivial delivery on demand. Known local edits can proceed directly. No mandatory plan file, JSON checkpoint, subagent or external skill installation is required.

## Installation

Use Python 3.11 or newer on a POSIX system. From this checkout:

```sh
python3 scripts/cdf.py validate --offline --json
python3 scripts/cdf.py install --target /path/to/project --dry-run --json
python3 scripts/cdf.py install --target /path/to/project --json
python3 scripts/cdf.py status --target /path/to/project --json
```

Installation makes no network or model calls. It installs 10 core skills (`cdf` and nine specialists), their references, two native agent templates, an optional-subskill catalog, and one managed AGENTS block. `--with-learning` adds explain and teach; `--with-operator` adds explicit model calibration. See the [bundle inventory](docs/bundle-inventory.md).

Global installation uses `--scope global` with the intended home as `--target`. `--home` selects an explicit alternative home for isolated testing; it must match the target. Project scope manages `<target>/AGENTS.md`; global scope manages `<home>/.codex/AGENTS.md`. Development and tests use temporary targets, never the developer's live configuration.

## Codex skill appearance and plugin packaging

Each skill includes `agents/openai.yaml` with a display name, short picker description, and an original CDF icon. These display fields are separate from the model-facing routing description in `SKILL.md`. Model calibration retains explicit-only invocation.

The offline installer copies skills into local folders, so Codex can still label them **Local file**. A source label such as **From Code Delivery Framework** belongs to a plugin installation; skill metadata cannot override provenance. The root `plugin.json` packages CDF as a skills-only plugin with a named interface. Install that package through a host-supported local/repository marketplace to test plugin discovery. See the [official packaging instructions](https://developers.openai.com/plugins/build/plugins) for marketplace setup; availability varies by host.

The plugin includes all 13 skills, including learning and explicit model calibration. It does not apply the managed AGENTS block, install native agent templates, or install the optional-subskill catalog. Use the offline installer when those integrations or selective extras are needed. Avoid enabling both copies of the same skills in one session. Plugin installation, exact source-label wording, and icon rendering have not been verified in the desktop picker. No live global configuration is changed by repository validation.

## Lifecycle

```sh
python3 scripts/cdf.py upgrade --target /path/to/project --dry-run --json
python3 scripts/cdf.py recover --target /path/to/project --dry-run --json
python3 scripts/cdf.py uninstall --target /path/to/project --dry-run --json
python3 scripts/cdf.py doctor --target /path/to/project --json
```

Inspect previews before omitting `--dry-run`. Upgrade retains extras unless explicitly disabled with `--without-learning` or `--without-operator`. Edited managed files block upgrades and are preserved on uninstall. `uninstall --release-modified-skills` preserves each modified skill and releases ownership. The installer preserves bytes outside its AGENTS block, unrelated configuration, and directories containing user files.

Legacy schema-2 installations with the frozen 12-core inventory remain readable and removable. A forward upgrade removes owned orchestration/planning/implementation files and installs the kernel; edited legacy files cause a conflict. The source version must be at least the recorded installed version. Upgrading a 1.1.0 installation changes the core inventory while retaining ownership safeguards. Newer-version downgrade attempts remain blocked. Inspect `status`, preview `upgrade`, resolve modified-file conflicts, and use `recover --dry-run` after interruption.

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

Completion reports distinguish COMPLETE (required acceptance and review observed), PARTIAL (named evidence or acceptance gaps), and BLOCKED (a missing decision, permission or capability prevents safe dependent work). Optional task-state schema enums remain internal. Hooks are not bundled or required.

Release, publishing and deployment require separate authorization. [sources.json](sources.json) and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES) preserve research provenance and licensing information.
