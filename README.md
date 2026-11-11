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

Installation makes no network or model calls. It installs one discoverable skill at `.agents/skills/cdf/`: the CDF entrypoint, nine core specialist modules and their references. The installer also supplies two native agent templates, an optional-subskill catalog, and one managed AGENTS block. `--with-learning` adds explain and teach modules; `--with-operator` adds explicit model calibration. Extras do not add visible skill entries. Source modules remain separate under `skills/` in this repository. See the [bundle inventory](docs/bundle-inventory.md).

Global installation uses `--scope global` with the intended home as `--target`. `--home` selects an explicit alternative home for isolated testing; it must match the target. Project scope manages `<target>/AGENTS.md`; global scope manages `<home>/.codex/AGENTS.md`. Development and tests use temporary targets, never the developer's live configuration.

## Codex skill appearance and plugin packaging

CDF has a display name, short description, a transparent small SVG for monochrome rendering, and a separate colored large PNG for the installed-skills card. These fields are separate from the model-facing routing description in `SKILL.md`. Desktop mention-picker inspection on 2026-11-10 found that skill-row icons come from artifact-template categories; that picker can still use a generic icon. A temporary-home app-server probe observed exactly one enabled CDF entry with resolved SVG/PNG paths. The settings-card rendering still needs verification after a real upgrade; discovery does not establish desktop rendering.

The offline installer can still appear as **Local file**. A named plugin source requires a plugin installation. Build a skills-only plugin from the same single-entry payload:

```sh
python3 scripts/package_cdf_plugin.py --output /path/to/new-cdf-plugin
# Optional: --with-learning --with-operator
```

The output parent must exist; an existing output directory is refused. The generated package contains `plugin.json`, the plugin icon, and `skills/cdf/` with its module index, guides, references and optional-subskill catalog. The manifest template is `templates/cdf-plugin.json`; do not install the repository root as a plugin, because its `skills/` folders are the separate authoring sources. Register the generated directory through a host-supported local/repository marketplace using the [official packaging instructions](https://developers.openai.com/plugins/build/plugins). The packaging command does not register, install, publish or modify global configuration. Host installation and exact source-label wording remain unverified.

A plugin improves distribution, identity and host-managed installation. It uses the same methods and does not establish higher reasoning quality. This skills-only plugin does not apply the AGENTS policy block or install native agent templates; the offline installer provides that fuller integration. Avoid enabling both copies of CDF in one session. Plugins and local installations now expose the same one skill; module names such as `cdf-debugging` are resolved through its index. Ask `$cdf` to debug or review rather than invoking a separate `$cdf-debugging` entry. Model calibration still requires an explicit request.

## Lifecycle

```sh
python3 scripts/cdf.py upgrade --target /path/to/project --dry-run --json
python3 scripts/cdf.py recover --target /path/to/project --dry-run --json
python3 scripts/cdf.py uninstall --target /path/to/project --dry-run --json
python3 scripts/cdf.py doctor --target /path/to/project --json
```

Inspect previews before omitting `--dry-run`. Upgrade retains extras unless explicitly disabled with `--without-learning` or `--without-operator`. Edited managed files block upgrades and are preserved on uninstall. `uninstall --release-modified-skills` preserves each modified skill and releases ownership. The installer preserves bytes outside its AGENTS block, unrelated configuration, and directories containing user files.

Existing schema-2 installations with the 10-core 1.2.x or frozen 12-core 1.1.0 inventory remain readable and removable. Upgrade migrates owned standalone skills into the single CDF folder, retains extras, and removes their old discoverable entrypoints. User files are preserved and modified managed files block migration. In the single layout, `--release-modified-skills` releases the whole CDF folder when any module is modified. A forward upgrade removes owned orchestration/planning/implementation files and installs the kernel; edited legacy files cause a conflict. The source version must be at least the recorded installed version. Upgrading a 1.1.0 installation changes the core inventory while retaining ownership safeguards. Newer-version downgrade attempts remain blocked. Inspect `status`, preview `upgrade`, resolve modified-file conflicts, and use `recover --dry-run` after interruption.

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

To check discovery without a model call or live configuration changes, run:

```sh
python3 scripts/check_cdf_discovery.py --codex /path/to/codex
```

This installs all modules in a temporary home/project and calls app-server `skills/list`. It checks one enabled CDF entry and valid icon paths. It does not test desktop rendering or specialist selection by a model.

See the [architecture guide](docs/architecture.md), [current acceptance limits](docs/status.md), and [evaluation protocol](evals/README.md). Static checks and fake adapters test mechanics, not model compliance. Live evaluations require explicit execution flags and trusted code. No verified OS sandbox provider, live behavioral acceptance, or subscription savings measurement is claimed.

Completion reports distinguish COMPLETE (required acceptance and review observed), PARTIAL (named evidence or acceptance gaps), and BLOCKED (a missing decision, permission or capability prevents safe dependent work). Optional task-state schema enums remain internal. Hooks are not bundled or required.

Release, publishing and deployment require separate authorization. [sources.json](sources.json) and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES) preserve research provenance and licensing information.
