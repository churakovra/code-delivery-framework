# Code Delivery Framework

CDF provides focused delivery skills for Codex. The root agent resolves material requirements, reuses project code, works directly by default, and delegates bounded work when independent review or another concrete benefit warrants it. The package version is defined in `[project].version` in `pyproject.toml`.

Adaptive delivery selects the next action from the accepted outcome, main uncertainty and risk. New functionality can start with a working vertical slice, then continue through the remaining scope. See [delivery strategy](skills/cdf/references/delivery-workflow.md). The current source is `2.0.0`. It is ready for installation and user acceptance; final native behavioral acceptance and comparative value are not established.

Ask naturally, for example: “Add order export using the existing access rules.” The agent inspects the current path, asks about material decisions the code and prior answers do not settle, implements a bounded change, and reports observed checks and gaps. The `cdf` kernel handles nontrivial delivery on demand. Known local edits can proceed directly. No mandatory plan file, JSON checkpoint, subagent or external skill installation is required.

## Install the Codex plugin

CDF has one installation path: a native Codex plugin. The portable profile provides eleven standalone skills without hooks, native roles, or managed `AGENTS.md` guidance. Use Python 3.11 or newer on POSIX to build a local package and marketplace catalog:

```sh
mkdir -p /path/to/marketplace/build /path/to/marketplace/.agents/plugins
python3 scripts/package_cdf_plugin.py --profile portable --output /path/to/marketplace/build/cdf-plugin-portable
cp templates/cdf-marketplace.example.json /path/to/marketplace/.agents/plugins/marketplace.json
```

Ensure the catalog's local source path points to the built package, then install it with Codex:

```sh
codex plugin marketplace add /path/to/marketplace --json
codex plugin add code-delivery-framework@cdf-local --json
codex plugin list --json
```

Restart Codex. Use `$cdf` to invoke the kernel explicitly. Without a mention, Codex may select a relevant discovered specialist based on the request; plugin installation does not force global CDF activation.

CDF includes display metadata and SVG/PNG assets. Host rendering varies;
resolved asset paths alone do not prove the appearance of a skill-picker row.

The output parent must exist; an existing output is refused. The package contains root `plugin.json`, assets, and eleven `skills/<name>/SKILL.md` entries. Learning adds two entries; operator adds explicit model calibration. Disabled extras are absent. Native plugin skills retain source bytes and references. The kernel also includes the optional-subskill catalog. No hooks, native agent configuration, private installer state or managed AGENTS policy is included. This command builds only; it does not register, install or publish.

For a local marketplace, place the built plugin at `build/cdf-plugin-portable` under a chosen marketplace root and copy [the example catalog](templates/cdf-marketplace.example.json) to that root's `.agents/plugins/marketplace.json`. Paths resolve from the marketplace root. Install explicitly with the target client's supported commands:

```sh
codex plugin marketplace add /path/to/marketplace-root --json
codex plugin add code-delivery-framework@cdf-local --json
codex plugin list --json
```

Those installation commands change the selected Codex home's plugin settings. Development probes use disposable HOME/CODEX_HOME only. The installed CLI uses `plugin add`, not `plugin install`. See the [official packaging contract](https://developers.openai.com/plugins/build/plugins).

The observed native names use the plugin namespace, for example `code-delivery-framework:cdf-architecture`. A specialist's metadata/discovery is distinct from an observed method result. Model calibration remains explicit-only. CLI/app-server discovery is verified separately from Desktop UI or other host surfaces; host behavior must be checked separately.

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
Personal definitions can be selected with explicit global scope and matching
`--target`/`--home` values; never apply globally without authorization.

Setup refuses a leftover legacy CDF manifest in the same scope and differing
unowned role files. It preserves identical preexisting files without adopting
them. Edited owned contents block updates/removal. Atomic transactions handle
interruption.

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
root `plugin.json`. The portable profile remains hook-free.

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
[installation and removal](docs/installation.md).

## Verification and development

The optional evaluation runner and synthetic fixtures are maintained separately on local branch `codex/cdf-2-evaluation-tooling` at commit `ec6c789d0724558eda6402f1bedf8a8567ad640e`. To inspect it, use `git worktree add /path/to/cdf-evaluation-tooling codex/cdf-2-evaluation-tooling`. Installation and runtime do not depend on that branch.

```sh
python3 scripts/validate_cdf.py
python3 scripts/cdf.py validate --offline --json
python3 -m unittest discover -s tests
```

To check discovery without a model call or live configuration changes, run:

```sh
python3 scripts/check_cdf_discovery.py --codex /path/to/codex
```

This installs the portable plugin in a temporary home and calls app-server `skills/list`. It checks the expected enabled plugin skills and valid icon paths. It does not test desktop rendering or specialist selection by a model.

See the [architecture guide](docs/architecture.md) and [evaluation protocol](evals/README.md). Static checks and fake adapters test mechanics, not model compliance. Live evaluations require explicit execution flags and trusted code. No verified OS sandbox provider, broad behavioral acceptance, or subscription savings measurement is claimed.

CDF checks the requested artifact or operation, with separate semantic, functional and visual evidence where applicable. Supported native progress reports meaningful checkpoints; skills cannot guarantee a particular host status line. No custom status runtime is installed. Prefer compatible installed visual specialists for new visual direction; absence uses the local fallback without downloads. Discovery, reading a guide, applying its method and observing an outcome are separate claims.

Completion reports distinguish COMPLETE (required acceptance and review observed), PARTIAL (named evidence or acceptance gaps), and BLOCKED (a missing decision, permission or capability prevents safe dependent work). Optional task-state schema enums remain internal. Hooks are not required; only the experimental desktop profile bundles them.

No root `LICENSE` is selected for this repository. Resolve licensing with the copyright owner before public distribution; MIT is a common option for an open-source Python/skills project, but must not be applied without that decision.

Release, publishing and deployment require separate authorization. [sources.json](sources.json) and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES) preserve research provenance and licensing information.

Native profile routing has narrow runtime evidence; broad behavioral impact remains unverified. Offline checks establish mechanics only. Live matched comparisons, host progress rendering and human visual acceptance remain required before claiming improved experience.

## Version and supported scope

`2.0.0` is the source/package version. It does not claim that all behavioral acceptance gates passed. The tested native client is
`codex-cli 0.167.0-alpha.4.1`. CLI/app-server plugin discovery, named-role routing
and optional Desktop event capture have separate bounded evidence. Other client
versions, Windows and full Desktop error-warning rendering are not established.
Skills guide the model; neither skills nor hooks provide a security boundary.

Invoke `$cdf` explicitly for the Engineering Partner kernel, or ask naturally: “Inspect the existing
publisher integration and recommend the smallest supported migration before
editing.” Standalone specialists may apply without first reading the root skill.
Use the explicit `profile --dry-run/--check/--apply` and `doctor --runtime`
examples above for configuration; those states are not execution proof.

See [installation and removal](docs/installation.md) for setup,
trust boundaries, recovery and removal. Final runtime acceptance remains open;
no comparative quality or usage-saving claim is made.
