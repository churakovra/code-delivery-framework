# Code Delivery Framework (experimental)

A portable instruction framework for shipping code with focused skills and a Python standard-library installer. Delivery coordinates the work. The master agent decomposes the task, works directly by default, and delegates when independent review, parallel ownership, specialist work, or diagnosis benefits the task. Runtime permissions and higher-priority instructions still govern execution.

## Workflow and context

The managed `AGENTS.md` block points to [delivery](https://github.com/churakovra/code-delivery-framework/blob/3ff534627e8b10de3dba2c6443855e870567ef84/skills/delivery/SKILL.md), which coordinates readiness, direct work or delegation, review, and completion. Skills guide specific work; `roles.json` combines required and conditional skills and resources. The [architecture and contribution guide](https://github.com/churakovra/code-delivery-framework/blob/3ff534627e8b10de3dba2c6443855e870567ef84/docs/architecture.md) describes ownership, role composition, master and subagent work, and creating skills. Read delivery once while its contents remain available, and reload it after relevant changes or context loss. Runtime restrictions and explicit user instructions take precedence.

For structural discovery, tracing and impact analysis, follow the [Codebase Memory route](https://github.com/churakovra/code-delivery-framework/blob/3ff534627e8b10de3dba2c6443855e870567ef84/skills/helpers/codebase-memory.md); it checks availability and coverage, verifies material claims in source and reports meaningful fallback limitations. Simple known-file edits and literal searches need no graph query. The `explain` skill supports explanations; `teach` is explicit-only for requested guided learning. Optional specialist candidates and their provenance and fallback are described in [subskills.json](https://github.com/churakovra/code-delivery-framework/blob/3ff534627e8b10de3dba2c6443855e870567ef84/subskills.json); they are not installed or guaranteed to be available. Selection and compliance are guidance, not runtime enforcement.

Delivery requires independent review for medium/high risk, more than three changed code files, or more than 50 added/deleted code lines, excluding generated files and documentation. If required review is unavailable, shipping is blocked. See [delivery](https://github.com/churakovra/code-delivery-framework/blob/3ff534627e8b10de3dba2c6443855e870567ef84/skills/delivery/SKILL.md) for risk, review, diagnosis and coordination rules, and [Git workflow](https://github.com/churakovra/code-delivery-framework/blob/3ff534627e8b10de3dba2c6443855e870567ef84/skills/helpers/git-workflow.md) for branch and commit boundaries.

## Installation and availability

Use Python 3.11 or newer:

```sh
python3.11 scripts/framework.py validate --target /path/to/project --offline
python3.11 scripts/framework.py install --target /path/to/project --dry-run
python3.11 scripts/framework.py install --target /path/to/project
```

Commands are `install`, `upgrade`, `recover`, `status`, `uninstall`, `validate`, `select-models`, `apply-models`, `sync-models`, and `inspect-role`. Shared options include `--target PATH`, `--global`, `--home PATH`, and `--codex PATH`. Install, upgrade, and uninstall support `--dry-run`. Only static `validate` supports `--offline`.

Installation uses the bundled provisional model policy, or an explicit TOML policy supplied with `install --model-policy PATH`. It validates the configured model/effort pairs against the runtime and stops when a required assignment is unavailable. It does not silently substitute models. Model research and task evaluations do not run during installation. The JSON selection report records whether the policy was bundled or supplied.

Install and upgrade fetch only the pinned Codebase Memory MCP release and its versioned integration skill. The archive checksum, binary version, and staged MCP protocol/tool availability are checked before target changes. Network access is required. Framework roles and helpers ship in this repository. The schema 2 `subskills.json` inventory describes the retained external integration, bundled helpers, and optional specialist candidates; role assignments live in `roles.json`.

After install or upgrade, the installer checks file state and requests `skills/list` with `forceReload` from the runtime. It checks enabled skill paths against installed paths. Availability is reported separately:

- `files`: managed and reused bytes are clean, or incomplete.
- `skills`: verified, incomplete, or unverified when the runtime check is unavailable.
- `mcp`: the staged protocol was checked; activation in the user's running session remains unverified.

These checks start no model task and run no task evaluation. A successful file transaction does not prove skill discovery or active MCP loading. Restart Codex, trust a project if required, and check the skill catalog and MCP server in a fresh session. Installation can report an incomplete discovery result without undoing the completed file transaction.

Fresh-session limitation observed in a temporary macOS home: the configured Codebase Memory server timed out during its MCP handshake under its default runtime settings. Supplying a newly created, short, private `CBM_RUNTIME_DIR` explicitly to the server allowed tool discovery in that test. The installer does not yet manage that runtime directory; automatic MCP activation is therefore not confirmed, and the workaround should be treated as diagnostic rather than a permanent configuration.

`status` includes a compact `summary` with file health, affected paths, and a next action; the detailed file and managed-block fields remain available for diagnosis. An archive revision marker is provenance supplied by the archive, not an authenticated checksum. Verify release artifacts through a trusted release channel before installing them.

For a release archive with an expanded revision marker, obtain its SHA-256 and full source revision independently from a trusted channel, then run `python3 scripts/verify_release.py /path/to/release.zip --sha256 TRUSTED_SHA256 --version VERSION --revision FULL_REVISION`. The verifier checks the whole archive's checksum and the version and revision inside it. A checksum supplied by the same untrusted archive does not authenticate that archive.

The verifier checks a private snapshot; keep the original archive unchanged between verification and extraction, or verify the bytes again before using them.

For global use, `--target` must equal the canonical configured home:

```sh
python3.11 scripts/framework.py install --global --target /Users/alex --home /Users/alex
```

A project installation manages `<target>/AGENTS.md`; a global installation manages `<home>/.codex/AGENTS.md`. Skills install under `<target>/.agents/skills/code-delivery-framework/`. No per-repository copy is needed for a global installation. State and recovery records remain in `.codex/delivery-framework/`. The installer never changes branches or creates commits or pull requests.

## Model policy

`.codex/delivery-framework/roles.json` maps roles to instructions, skills, and policy keys. `.codex/delivery-framework/model-policy.toml` maps keys to models and reasoning efforts. The master agent uses the current chat model for work it owns. Policy files cannot change an already-running agent.

Inspect an installed role with `python3 scripts/framework.py inspect-role --target /path/to/project --role implementation` (use the installation's global options when applicable). This read-only view lists the configured skills, conditional resources, source paths and model policy. File presence and configured settings do not verify runtime discovery, active model settings or MCP activation.

For delegated work, delivery reads the current registry and policy at launch. It requests a generic agent with explicit model/effort where supported. Before using a fixed named role, it compares the runtime-advertised model and effort with the policy; both must match. It records requested settings and available runtime evidence, distinguishing requests from confirmed active settings. Unknown or mismatched settings make that delegation unavailable when a matching explicit launch is unavailable. Files on disk alone do not prove active settings.

Research is explicit and may consume account usage:

```sh
python3.11 scripts/framework.py select-models --target /path/to/project --selection-profile /path/to/profile.toml > proposal.json
python3.11 scripts/framework.py apply-models --target /path/to/project --proposal proposal.json
```

`--selection-profile` applies only to `select-models`. Supply plan, workload, priorities, and preferences in TOML. The report retains the profile, so do not include secrets. `select-models` creates a proposal without changing the target. `apply-models` validates and applies it transactionally. Both stop on conflicts. Ordinary upgrades retain the installed policy and do not reselect.

After manually editing the installed policy, run `sync-models` with the installation's target and scope, then restart Codex. It checks model availability, refuses modified role files, and updates the manifest transactionally. Upgrade stops on unsynchronized policy edits. Historical selection reports do not describe later manual policy changes. `model-policy.md` is a fillable draft, not runtime configuration.

## Upgrade, recovery, and fresh installation

The 0.6 architecture requires a fresh installation when the existing version is unknown or earlier than 0.6. The installer rejects that upgrade instead of migrating it. Upgrades from 0.6 or later remain supported; use the same `--target`, `--home`, and `--global` scope as the installation. An unsupported or damaged manifest stops for manual resolution.

For an older installation, run its `status` and, if a transaction was interrupted, `recover` before proceeding. Back up its model policy and any local changes outside the installation target. Inspect `uninstall --dry-run`, then use the old installation's uninstaller and inspect the result. Uninstall preserves modified and reused files and Codebase Memory indexes. Resolve remaining conflicts without discarding user-owned content; do not assume uninstall removed everything. Run the new version's `install --dry-run`, review conflicts, and then install. Supply the backed-up model policy with `--model-policy` if appropriate; the new installer validates its model/effort pairs and does not silently substitute unavailable models.

For a supported upgrade, inspect `status` and run `upgrade --dry-run` first. The preview reports local managed-file and bundled-name conflicts and may be incomplete: it does not download dependencies, probe Codex, or check every dependency and runtime conflict. `--deep-preview` additionally downloads and verifies dependencies and plans file operations, but does not establish runtime model availability or activation. The actual operation repeats its checks; preserve local changes and resolve conflicts before proceeding. The installed model policy is retained for supported upgrades.

`status` reports the recorded version, source identity, file health, managed-block health and recovery state. A missing version is unknown, not proof of a compatible installation. The source version is in `pyproject.toml`; a dirty source checkout is not identified by its revision alone. If a transaction was interrupted, run `recover` using the original target and scope before retrying; recovery stops when files changed after the transaction began. After install or upgrade, inspect `status`, restart Codex and verify skill discovery and MCP activation in a fresh session. The installer preserves bytes outside managed instruction blocks and reports conflicting unowned instructions for manual resolution.

## Verification and context budgets

Installer development uses automated regression checks against temporary targets. Installation itself checks availability without running those tests or evaluating agents. Real task evaluations and token benchmarks remain optional and explicit. Automated routing checks inspect instruction contracts; they do not prove model compliance.

Historical evidence for an earlier revision (2026-10-29; not evidence for 0.6): 104 automated tests passed, including temporary-target lifecycle, policy, migration, discovery-reporting, and static guidance checks. A live temporary project exercise downloaded and verified the pinned dependency, installed the payload, confirmed clean files and discovery of all 13 installed skills through Codex, upgraded, and uninstalled. This exercise called the installation routines directly; CLI policy behavior is covered by automated tests. Independent review found no actionable defects. Active MCP loading in a user's session, platform archives other than macOS ARM64, model compliance, and token savings remain unverified. No model task evaluation ran.

Installer structure assessment: version and source identity are in `scripts/framework_identity.py`, command parsing and dispatch are in `scripts/framework_cli.py`, pinned dependencies and their staged checks are in `scripts/framework_dependencies.py`, and transactional recovery and policy operations remain in `scripts/framework.py`. Removing recovery, conflict detection, dependency verification, or model compatibility checks would change documented safety or runtime behavior. This revision retains those capabilities; it does not claim an 80–90% reduction or a complete decomposition. Further extraction can be done without changing the lifecycle contract.

Maintainability budgets are 300 words for the managed instructions, 700 for delivery, 250 for each role entrypoint, 400 for each helper, and under 100 for routine communication rules. The specialized, explicitly invoked model-routing skill is exempt from the role-entrypoint budget.

Instruction size is not a measurement of tokens or subscription savings. Catalog metadata, task context, tool output, retries, and runtime behavior also affect usage. The static guidance checks enforce entrypoint word budgets, but do not measure task outcomes.

Manual acceptance: confirm the managed block occurs once, `status` reports clean files, the fresh session discovers framework skills, and its MCP server is active. An optional small authorized task can then check role/helper selection and review behavior. Agents perform bounded local UI verification when needed and permitted; report any remaining user acceptance.

## Source and licensing

Framework skills and helpers are original concise adaptations. `sources.json` retains inspected revisions, licenses, and research purposes. `THIRD_PARTY_NOTICES` records attribution and limitations. Replaced upstream workflow skills are research references, not installation dependencies. The separately fetched Codebase Memory integration retains its upstream license and notices.
