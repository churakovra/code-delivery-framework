# Code Delivery Framework

CDF provides focused delivery skills for Codex. The root agent resolves material requirements, reuses project code, works directly by default, and delegates bounded work when independent review or another concrete benefit warrants it. The package version is defined in `[project].version` in `pyproject.toml`.

Adaptive delivery selects the next action from the accepted outcome, main uncertainty and risk. New functionality can start with a working vertical slice, then continue through the remaining scope. See [delivery strategy](skills/cdf/references/delivery-workflow.md). The current source is the `2.1.0` candidate. Packaging and runtime discovery are checked separately from behavioral acceptance; comparative value remains unestablished.

Ask naturally, for example: “Add order export using the existing access rules.” The agent inspects the current path, asks about material decisions the code and prior answers do not settle, implements a bounded change, and reports observed checks and gaps. The `cdf` kernel handles nontrivial delivery on demand. Known local edits can proceed directly. No mandatory plan file, JSON checkpoint, subagent or external skill installation is required.

Interaction intent comes before delivery depth. Explanation, teaching, research, review and planning use safe reads and diagnostics without autonomous project edits. Implementation requests allow scoped changes. Teaching leaves steps to the learner; a failure report preserves that mode, while an explicit request to implement switches authority without reopening settled choices. These instructions guide behavior; they do not enforce permissions.

`cdf-testing` owns regression design, credible test boundaries and preservation of unique guarantees during cleanup. `cdf-verification` owns fresh command/results evidence. Architecture guidance filters reference features by target requirements and challenges speculative complexity.

## Install from GitHub

CDF has one plugin identity, `code-delivery-framework`: 14 core skills and
three native context hooks. Install Python 3.11+ and a Codex client with native
plugin support. For this candidate, use the PR branch:

```sh
git clone --branch codex/cdf-2.1.0 https://github.com/churakovra/code-delivery-framework.git
cd code-delivery-framework
mkdir -p build/marketplace/.agents/plugins
python3 scripts/package_cdf_plugin.py --output build/marketplace/cdf-plugin
cp templates/cdf-marketplace.example.json build/marketplace/.agents/plugins/marketplace.json
codex plugin marketplace add "$PWD/build/marketplace" --json
codex plugin add code-delivery-framework@cdf-local --json
```

This uses the existing packager and native plugin manager. No generated bundle,
installer service, global AGENTS policy or native roles are committed/installed.
The output directory must be new. The builder identifies `codex` on PATH;
`--codex /absolute/path/to/codex` selects the target client explicitly.
The canonical manifest uses root `plugin.json` and
`extensions.com.openai.hooks`, plus a compatibility overlay referring to the
same hook file. For the observed 0.167.0-alpha.4.1 and 0.169.0-alpha.11.1 clients,
root manifests suppress hook discovery; the builder emits compatibility-only
layout with the same identity. No distribution-profile choice is needed.
Old `--profile portable` / `--profile desktop-controlled` flags are aliases for
this single plugin. `--with-learning` is a deprecated no-op; `--with-operator`
explicitly adds model calibration. Source skill bytes and references are retained.

Restart Codex and review/trust the three commands using `/hooks` (or Settings >
Hooks / Review hooks in the desktop app). Installation does not grant hook trust.
If an old `code-delivery-framework-desktop` plugin is enabled, remove it explicitly;
CDF never changes another installation automatically. Without trusted hooks,
skills remain available on demand, including explicit `$cdf`, but the ongoing
Engineering Partner context is not delivered.

```sh
python3 scripts/cdf.py doctor --target "$PWD" --runtime --json
```

Doctor separates installation, 14-skill discovery, hook trust, execution history,
context emission and method application. Use `--plugin-data /explicit/native/data`
and optionally `--session-id ID` to inspect only selected bounded history.
`READY_NOT_EXECUTION_PROOF` is capability readiness, not proof that a model
received context or applied a skill. See [installation and update details](docs/installation.md).

## Optional tools and model policy

[subskills.catalog.json](subskills.catalog.json) lists optional research candidates, triggers, provenance and local fallbacks. It does not load or install them. `integrations list` and `integrations plan codebase-memory-mcp` are informational. Verify source, license and runtime compatibility before separate installation.

[policies/model-routing.example.toml](policies/model-routing.example.toml) is advisory. It records candidate model/effort pairs, worker budgets and fallback rules; it cannot change a running agent's configuration. Native worker/explorer remain runtime choices; the custom reviewer and diagnostician templates contain no model pins.

### Optional native agent profiles

`policies/native-agents.example.toml` contains editable candidates for three
standard Codex roles: `cdf_explorer`, `cdf_reviewer`, and `cdf_diagnostician`.
`budget`, `balanced`, and `quality` are selection labels, not measured rankings.
The plugin does not install these files automatically.

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

## Native Engineering Partner context

`SessionStart` supplies a compact operating contract: intent and authority first,
decisions before code, relevant skills before substantial work, completion of
accepted outcomes and evidence before claims. It covers startup, resume, clear,
compact and fork. `UserPromptSubmit` refreshes intent, settled decisions and
specialist routing. `SubagentStart` supplies bounded child guidance; the parent
still passes concrete tasks, authority, decisions and completion criteria.

One Python standard-library handler emits deterministic `additionalContext`.
It does not classify prompts, read source/transcripts, call models or services,
load every skill or grant permissions. Codex permissions, approvals and sandbox
remain authoritative. No PreToolUse/Stop guard or custom orchestration is added.

After stdout emission, allowlisted event/session/time/context-hash metadata may
be appended to native `PLUGIN_DATA/events.jsonl` (0600, about 1 MiB maximum).
No prompts, model answers, source, tool arguments or transcripts are stored.
Missing/full history does not prevent context output and is reported separately.
History is not current model receipt or intellectual application. Windows and
other unobserved clients remain unverified. Behavior testing belongs to the user.

## Verification and development

Existing evaluation tooling is described in [the evaluation protocol](evals/README.md). The candidate runner packages and installs the native plugin in an isolated Codex home; it adds no behavioral cases. Manual behavioral acceptance remains pending.

```sh
python3 scripts/validate_cdf.py
python3 scripts/cdf.py validate --offline --json
python3 -m unittest discover -s tests
```

To check discovery without a model call or live configuration changes, run:

```sh
python3 scripts/check_cdf_discovery.py --codex /path/to/codex
```

This installs the unified plugin in a temporary home and calls native `skills/list` and `hooks/list`. It checks enabled skills, icon paths, hook counts and trust without granting trust or invoking a model.

See the [architecture guide](docs/architecture.md) and [evaluation protocol](evals/README.md). Static checks and fake adapters test mechanics, not model compliance. Live evaluations require explicit execution flags and trusted code. No verified OS sandbox provider, broad behavioral acceptance, or subscription savings measurement is claimed.

CDF checks the requested artifact or operation, with separate semantic, functional and visual evidence where applicable. Supported native progress reports meaningful checkpoints; skills cannot guarantee a particular host status line. No custom status runtime is installed. Prefer compatible installed visual specialists for new visual direction; absence uses the local fallback without downloads. Discovery, reading a guide, applying its method and observing an outcome are separate claims.

Completion reports distinguish COMPLETE (required acceptance and review observed), PARTIAL (named evidence or acceptance gaps), and BLOCKED (a missing decision, permission or capability prevents safe dependent work). Optional task-state schema enums remain internal. Hook trust is required for ongoing context delivery; skills remain available without hooks.

No root `LICENSE` is selected for this repository. Resolve licensing with the copyright owner before public distribution; MIT is a common option for an open-source Python/skills project, but must not be applied without that decision.

Release, publishing and deployment require separate authorization. [sources.json](sources.json) and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES) preserve research provenance and licensing information.

Native profile routing has narrow runtime evidence; broad behavioral impact remains unverified. Offline checks establish mechanics only. Live matched comparisons, host progress rendering and human visual acceptance remain required before claiming improved experience.

## Version and supported scope

`2.1.0` is the source/package candidate version. It does not claim that all behavioral acceptance gates passed. The tested native client is
`codex-cli 0.167.0-alpha.4.1` for prior role/hook observations; candidate plugin discovery was checked with `codex-cli 0.169.0-alpha.11.1`. CLI/app-server plugin discovery, named-role routing
and hook discovery have separate bounded evidence. Other client
versions, Windows and full Desktop error-warning rendering are not established.
Skills guide the model; neither skills nor hooks provide a security boundary.

Invoke `$cdf` explicitly for the Engineering Partner kernel, or ask naturally: “Inspect the existing
publisher integration and recommend the smallest supported migration before
editing.” Standalone specialists may apply without first reading the root skill.
Use the explicit `profile --dry-run/--check/--apply` and `doctor --runtime`
examples above for configuration; those states are not execution proof.

See [installation and removal](docs/installation.md) for setup,
trust boundaries, recovery and removal. Manual behavioral acceptance remains open;
no comparative quality or usage-saving claim is made.
