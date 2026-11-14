# Code Delivery Framework

CDF provides focused delivery skills for Codex. The root agent resolves material requirements, reuses project code, works directly by default, and delegates bounded work when independent review or another concrete benefit warrants it. The package version is defined in `[project].version` in `pyproject.toml`.

Adaptive delivery selects the next action from the accepted outcome, main uncertainty and risk. New functionality can start with a working vertical slice, then continue through the remaining scope. See [delivery strategy](skills/cdf/references/delivery-workflow.md). The current source is the unreleased `2.0.0-rc1` review candidate. It is experimental: final native behavioral acceptance and comparative value are not yet established.

Ask naturally, for example: “Add order export using the existing access rules.” The agent inspects the current path, asks about material decisions the code and prior answers do not settle, implements a bounded change, and reports observed checks and gaps. The managed policy supplies short always-on safeguards; the `cdf` kernel handles nontrivial delivery on demand. Known local edits can proceed directly. No mandatory plan file, JSON checkpoint, subagent or external skill installation is required.

## Installation

Use Python 3.11 or newer on a POSIX system. From this checkout:

```sh
python3 scripts/cdf.py validate --offline --json
python3 scripts/cdf.py install --target /path/to/project --dry-run --json
python3 scripts/cdf.py install --target /path/to/project --json
python3 scripts/cdf.py status --target /path/to/project --json
```

Installation makes no network or model calls. It installs one discoverable skill at `.agents/skills/cdf/`: the CDF entrypoint, ten core specialist modules and their references. The installer also supplies two native agent templates, an optional-subskill catalog, and one managed AGENTS block. `--with-learning` adds explain and teach modules; `--with-operator` adds explicit model calibration. Extras do not add visible skill entries. Source modules remain separate under `skills/` in this repository. The canonical inventory is `cdf_registry.py`.

Global installation uses `--scope global` with the intended home as `--target`. `--home` selects an explicit alternative home for isolated testing; it must match the target. Project scope manages `<target>/AGENTS.md`; global scope manages `<home>/.codex/AGENTS.md`. Development and automated tests use disposable targets.

## Codex skill appearance and plugin packaging

CDF includes display metadata and SVG/PNG assets. Host rendering varies;
resolved asset paths alone do not prove the appearance of a skill-picker row.

The offline installer can still appear as **Local file** and retains one visible kernel with compact modules. The portable plugin now packages standalone native skills:

```sh
python3 scripts/package_cdf_plugin.py --profile portable --output /path/to/new-cdf-plugin
# Optional: --with-learning --with-operator
```

The output parent must exist; an existing output is refused. The package contains root `plugin.json`, assets, and eleven `skills/<name>/SKILL.md` entries. Learning adds two entries; operator adds explicit model calibration. Disabled extras are absent. Native plugin skills retain source bytes and references. The kernel also includes the optional-subskill catalog. No hooks, native agent configuration, private installer state or managed AGENTS policy is included. This command builds only; it does not register, install or publish.

For a local marketplace, place the built plugin at `build/cdf-plugin-portable` under a chosen marketplace root and copy [the example catalog](templates/cdf-marketplace.example.json) to that root's `.agents/plugins/marketplace.json`. Paths resolve from the marketplace root. Install explicitly with the target client's supported commands:

```sh
codex plugin marketplace add /path/to/marketplace-root --json
codex plugin add code-delivery-framework@cdf-local --json
codex plugin list --json
```

Those installation commands change the selected Codex home's plugin settings. Development probes use disposable HOME/CODEX_HOME only. The installed CLI uses `plugin add`, not `plugin install`. See the [official packaging contract](https://developers.openai.com/plugins/build/plugins).

The observed native names use the plugin namespace, for example `code-delivery-framework:cdf-architecture`. A specialist's metadata/discovery is distinct from an observed method result. Model calibration remains explicit-only. CLI/app-server discovery is verified separately from Desktop UI or other host surfaces; host behavior must be checked separately.

Before migrating, inspect existing project and global CDF installations. Do not enable a plugin beside a legacy `cdf` copy: both can influence the same task. Preserve the installed version/source and user files, preview `uninstall --dry-run` against the correct legacy scope, resolve modified-file conflicts, and only then uninstall the owned legacy copy and enable the plugin. Uninstall preserves bytes outside managed blocks and user-modified files; verify no conflicting CDF skill remains before enabling. To roll back, remove the plugin with `codex plugin remove code-delivery-framework@cdf-local --json`, then reinstall the preserved legacy distribution after previewing it. No migration command here automatically edits global settings or discards user files.

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

### Optional native agent profiles

`policies/native-agents.example.toml` contains editable candidates for three
standard Codex roles: `cdf_explorer`, `cdf_reviewer`, and `cdf_diagnostician`.
`budget`, `balanced`, and `quality` are selection labels, not measured rankings.
The portable plugin does not install these files automatically.

```sh
python3 scripts/cdf.py profile --target /path/to/project --policy policies/native-agents.example.toml --dry-run --json
python3 scripts/cdf.py profile --target /path/to/project --policy policies/native-agents.example.toml --check --json
python3 scripts/cdf.py profile --target /path/to/project --policy policies/native-agents.example.toml --apply --json
python3 scripts/cdf.py profile --target /path/to/project --rollback --dry-run --json
```

Preview is offline. Check queries the native model catalog and agents-enabled
setting; `available_advertised` is not proof that a role loaded or executed.
Apply checks capabilities again, installs native TOMLs and reports `configured`
with `runtime_routing: NOT_OBSERVED`. Unknown pairs block setup; no silent
fallback is applied. Successful execution must be evidenced separately.

Project trust remains under Codex/user control. On the tested CLI, an untrusted
Git project did not expose its custom role; the same trusted setup executed it.
CDF does not grant trust or rewrite `config.toml`. Restart in the intended trusted
project and use a fresh bounded context when verifying role/model bindings.
Personal definitions can be selected with explicit global scope and the same
`--target`/`--home` rules as the legacy installer; never apply globally without
authorization.

Setup refuses a legacy CDF manifest in the same scope and differing unowned role
files. It preserves identical preexisting files without adopting them. Edited
owned contents block updates/removal. Existing CDF locks, atomic transactions and
`recover` handle interruption; no second recovery engine is installed.

`profile --rollback` removes only role files created by this setup and its
ownership receipt. It preserves preexisting roles and the private-state ignore
block. It does **not** restore the last successfully applied profile after a
profile change; reselect a preserved policy/profile explicitly for that purpose.
Interrupted operations can restore their preimages through `recover`.

## Optional desktop observation (bounded runtime support)

The optional `desktop-controlled` build adds three metadata-only hooks:
SessionStart and CDF SubagentStart/Stop. It is separately named
`code-delivery-framework-desktop`. It uses the documented compatibility manifest
`.codex-plugin/plugin.json`: the tested native client ignored bundled hooks in
root `plugin.json`. Portable and legacy defaults remain hook-free.

```sh
python3 scripts/package_cdf_plugin.py --profile desktop-controlled --output /existing/parent/cdf-desktop
python3 scripts/cdf.py doctor --target /path/to/project --runtime --codex /path/to/codex --json
python3 scripts/cdf.py doctor --target /path/to/project --runtime --codex /path/to/codex --plugin-data /explicit/native/plugin/data --session-id ID --json
```

Building does not register the plugin or grant trust. Review hooks through the
host's native `/hooks` flow. Do not enable both CDF plugin variants in ordinary
use; their skill inventories overlap. Existing installations are never disabled
automatically. Native discovery distinguishes enabled/trusted from execution;
selected log records establish historical observations only. No enforcement or
skill activation is inferred. Effective model is stored only when an actual
hook supplies it; effort stays unknown.

The observer writes only allowlisted IDs, role, model, event and timestamp to
`PLUGIN_DATA/events.jsonl` (0600). It never reads source/transcripts or stores
commands, tool output or assistant messages. The reserved log stops at about
1 MiB and reports degradation instead of deleting history. Doctor also reports
a full valid log as degraded while retaining its historical observations. Inspect/archive or
remove that file explicitly to start a new log. A two-second native timeout
bounds each hook. The observer requires only Python standard-library features; the framework CLI/doctor requires Python ≥3.11. Confirm the interpreter in the actual Codex shell. Windows is unverified. No PostToolUse collector or guardrail is shipped.

SessionStart returns compact version/profile/mode context; configured role files
are not proof of agent availability or routing. New host behavior, warning
rendering and full-host overhead require runtime acceptance. See
[installation, migration and removal](docs/installation.md).

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

See the [architecture guide](docs/architecture.md) and [evaluation protocol](evals/README.md). Static checks and fake adapters test mechanics, not model compliance. Live evaluations require explicit execution flags and trusted code. No verified OS sandbox provider, broad behavioral acceptance, or subscription savings measurement is claimed.

CDF checks the requested artifact or operation, with separate semantic, functional and visual evidence where applicable. Supported native progress reports meaningful checkpoints; skills cannot guarantee a particular host status line. No custom status runtime is installed. Prefer compatible installed visual specialists for new visual direction; absence uses the local fallback without downloads. Discovery, reading a guide, applying its method and observing an outcome are separate claims.

Completion reports distinguish COMPLETE (required acceptance and review observed), PARTIAL (named evidence or acceptance gaps), and BLOCKED (a missing decision, permission or capability prevents safe dependent work). Optional task-state schema enums remain internal. Hooks are not required; only the experimental desktop profile bundles them.

Release, publishing and deployment require separate authorization. [sources.json](sources.json) and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES) preserve research provenance and licensing information.

The legacy single-entry layout remains available. Native profile routing has narrow runtime evidence; broad behavioral impact remains unverified. Older installers reject the single-layout manifest field; use the current installer for recovery and removal. Offline tests establish mechanics only. Live matched comparisons, host progress rendering and human visual acceptance remain required before claiming improved experience.

## Review candidate and supported scope

`2.0.0-rc1` is a prerelease candidate, not a published release or a claim
that all 2.0 gates passed. The tested native client is
`codex-cli 0.167.0-alpha.4.1`. CLI/app-server plugin discovery, named-role routing
and optional Desktop event capture have separate bounded evidence. Other client
versions, Windows and full Desktop error-warning rendering are not established.
Skills guide the model; neither skills nor hooks provide a security boundary.

Try `$cdf` for a nontrivial delivery task, or ask naturally: “Inspect the existing
publisher integration and recommend the smallest supported migration before
editing.” Standalone specialists may apply without first reading the root skill.
Use the explicit `profile --dry-run/--check/--apply` and `doctor --runtime`
examples above for configuration; those states are not execution proof.

See [installation, migration and removal](docs/installation.md) for setup,
trust boundaries, recovery and removal. Final runtime acceptance remains open;
no comparative quality or usage-saving claim is made.
