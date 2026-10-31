# Code Delivery Framework (experimental)

A portable instruction framework for shipping code with focused skills and a Python standard-library installer. Delivery coordinates the work. The master agent decomposes the task, works directly by default, and delegates when independent review, parallel ownership, specialist work, or diagnosis benefits the task. Runtime permissions and higher-priority instructions still govern execution.

## Workflow and context

The managed `AGENTS.md` block points to delivery and states shared boundaries. Delivery owns sequencing, risk, delegation, review, and completion. A role skill defines how to perform its assigned work. A helper supplies a narrow technique only when its activation condition matches.

Read delivery once while its contents remain available. Load only the active role and applicable helpers. Reread after relevant changes or context loss. Helpers are Markdown references under `skills/helpers/`, not separate automatically triggered skills. Installation no longer downloads broad external workflow skills such as `asd-ste100`, systematic debugging, or TDD. The shared instructions contain concise communication rules; an optional communication helper handles ambiguity-sensitive text. Explicit user requests for separately installed skills remain authoritative.

The `specialist_skills` section of [subskills.json](subskills.json) is a curated set of optional existing skills, with activation, roles, provenance, and local fallbacks. The master agent considers matching entries for its own work and delegated assignments; subagents verify availability in their runtime catalog before reading a selected skill. The registry does not install or enable these skills, pin an independently installed version, or guarantee their selection. The recorded source revision is the revision researched, not proof of the installed version. When a candidate is unavailable, use the local fallback and disclose any material capability gap. Load specialist instructions only when their additional depth helps; user requests and higher-priority instructions prevail.

Keep one compact checkpoint: objective, baseline, acceptance, ownership, risk, evidence, and next action. Small tasks need no separate planning artifact. For substantial work, conduct a short requirements interview when runtime rules permit; use existing answers and evidence to avoid repeating questions. Use project-authoritative checks and meaningful regression coverage. Universal TDD cycles are not required. For structural discovery, tracing or impact analysis, check Codebase Memory availability and use it when suitable, with source fallback for insufficient coverage or unavailable tools.

Delivery runs a task loop: select the next action and applicable skills, inspect results, update the checkpoint, and continue until acceptance is evidenced or a concrete blocker prevents further authorized progress. Partial work and failed approaches do not end the task while useful work remains. Ask for missing information or consequential decisions, continue independent work while waiting, and resume dependent work when answered.

Before work, the master agent identifies responsibilities and dependencies and chooses direct work, a sequence of role-assigned subagents, or a mix. Simple tasks need no formal decomposition artifact; revisit the choice as the task changes. Only the master agent launches subagents. It supplies a compact ownership brief, relevant source locations, acceptance criteria, constraints, and current evidence. It uses their evidence and assigns follow-up when needed. Subagents may ask the user when the runtime permits, or relay questions to the master agent; they do not launch more agents. Runtime instructions and available tools may restrict delegation or questions.

Independent review is required for medium or high risk, more than three changed code files, or more than 50 added/deleted code lines. Exclude generated files and documentation from size counts. Medium risk includes cross-component behavior and nontrivial failure handling. High risk includes authentication, permissions, money, persistent-data integrity, migrations, concurrency, shared contracts, and broad lifecycle changes. The reviewer inspects the actual diff, callers, failure paths, and raw check output. Substantive repairs require updated review. If required review is unavailable, prepare the authorized patch and checks, then report shipping as blocked. After two failed repairs of one acceptance failure, obtain independent diagnosis before another fix.

The framework retains explicit authorization requirements for staging, branches, commits, pull requests, merges, publishing, releases, and deployment.

## Installation and availability

Use Python 3.11 or newer:

```sh
python3.11 scripts/framework.py validate --target /path/to/project --offline
python3.11 scripts/framework.py install --target /path/to/project --dry-run
python3.11 scripts/framework.py install --target /path/to/project
```

Commands are `install`, `upgrade`, `recover`, `status`, `uninstall`, `validate`, `select-models`, `apply-models`, and `sync-models`. Shared options include `--target PATH`, `--global`, `--home PATH`, and `--codex PATH`. Install, upgrade, and uninstall support `--dry-run`. Only static `validate` supports `--offline`.

Installation uses the bundled provisional model policy, or an explicit TOML policy supplied with `install --model-policy PATH`. It validates the configured model/effort pairs against the runtime and stops when a required assignment is unavailable. It does not silently substitute models. Model research and task evaluations do not run during installation. The JSON selection report records whether the policy was bundled or supplied.

Install and upgrade fetch only the pinned Codebase Memory MCP release and its versioned integration skill. The archive checksum, binary version, and staged MCP protocol/tool availability are checked before target changes. Network access is required. Framework roles and helpers ship in this repository. The schema 2 `subskills.json` inventory distinguishes the retained external integration, bundled helpers, and optional specialist candidates.

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

For delegated work, delivery reads the current registry and policy at launch. It requests a generic agent with explicit model/effort where supported. Before using a fixed named role, it compares the runtime-advertised model and effort with the policy; both must match. It records requested settings and available runtime evidence, distinguishing requests from confirmed active settings. Unknown or mismatched settings make that delegation unavailable when a matching explicit launch is unavailable. Files on disk alone do not prove active settings.

Research is explicit and may consume account usage:

```sh
python3.11 scripts/framework.py select-models --target /path/to/project --selection-profile /path/to/profile.toml > proposal.json
python3.11 scripts/framework.py apply-models --target /path/to/project --proposal proposal.json
```

`--selection-profile` applies only to `select-models`. Supply plan, workload, priorities, and preferences in TOML. The report retains the profile, so do not include secrets. `select-models` creates a proposal without changing the target. `apply-models` validates and applies it transactionally. Both stop on conflicts. Ordinary upgrades retain the installed policy and do not reselect.

After manually editing the installed policy, run `sync-models` with the installation's target and scope, then restart Codex. It checks model availability, refuses modified role files, and updates the manifest transactionally. Upgrade stops on unsynchronized policy edits. Historical selection reports do not describe later manual policy changes. `model-policy.md` is a fillable draft, not runtime configuration.

## Upgrade, recovery, and migration

Use `upgrade` with the same `--target`, `--home`, and `--global` values as installation. `status` reports recorded file state. If a transaction was interrupted, run `recover` against that target before retrying. Recovery stops if a file changed after the transaction began.

To find the installed version, open `.codex/delivery-framework/manifest.json` in the installation target and look for `framework_version` near the top. For a global installation, the path is `~/.codex/delivery-framework/manifest.json` (or under the `--home` used at installation). `status` also returns this field; `null` or a missing field means the older installation did not record a version. The source's `pyproject.toml` supplies the version; a `.dev` suffix identifies development code rather than a published release. For a Git checkout, source identity records HEAD and whether the checkout had changes; a dirty checkout is not identified by the revision alone. Git-generated archives can include an expanded `SOURCE_REVISION` marker. The marker identifies the claimed source revision but is not a signature or a verification of the archive's integrity; archives without an expanded marker report an unknown revision. Upgrades retain the current model policy and reject a downgrade when both versions are known. Reinstalling the same version with `upgrade` is permitted. Existing schema 1 and 2 manifests remain readable; unsupported schemas stop for manual resolution.

Before an upgrade, inspect `status` and run `upgrade --dry-run` with the same target and scope. The preview reports locally detected managed-file and bundled skill-name conflicts, a partial list of bundled changes, and whether its assessment is blocked or incomplete. It does not download dependencies, probe Codex, or check dependency skill names or all dependency, runtime, and migration conflicts. Resolve conflicts without discarding local edits, then run the upgrade; it checks again before writing. Confirm the version and file state afterward. `managed_blocks` distinguishes modifications to framework-owned instruction and configuration blocks from changes elsewhere in those files. Skill discovery and active MCP loading are separate checks, and may require a new Codex session. The runtime `roles.json` is generated from the source registry and installed policy, so its structure differs from the source file.

Add `--deep-preview` to an install or upgrade dry run to download and verify the pinned dependencies and run the full file-planning checks without writing the target. It reports planned additions, updates, removals, unchanged files, and reused files. The preview does not probe Codex or verify runtime model availability and activation. Files can change after the preview, so the real operation repeats its checks.

Upgrade removes obsolete framework-owned external skill files only when unchanged. Modified managed files cause a conflict that must be resolved without discarding user work. User-owned reused skills remain user-owned. `uninstall --dry-run` identifies preserved changes. Uninstall preserves reused files and Codebase Memory indexes.

For an agent performing an upgrade:

1. Obtain the requested release source and identify the installation target and scope. Do not assume the latest checkout is the requested release.
2. Run `status`. If recovery is required, run `recover` first; preserve any files that recovery reports as changed. If the installed version is unknown, report it as unknown.
3. Read the target release's migration notes. Run `upgrade --dry-run` with the original target and scope, and inspect every conflict and incomplete check. A successful preview is not a guarantee that the transaction will succeed.
4. Preserve modified managed files and resolve ownership conflicts before proceeding. Do not overwrite local changes or silently uninstall user-owned content. The existing model policy is retained; incompatible models require explicit resolution.
5. Run `upgrade`. Schema 1 and 2 manifests are migrated by the installer; an unsupported or damaged manifest stops the operation. A known downgrade is blocked, while reinstalling the same version and skipping releases are permitted only when the installer accepts the existing state and the release migration notes allow it.
6. Run `status` again and report the recorded version, source identity, file and block state, and any incomplete availability checks. Restart Codex and verify discovery and MCP activation separately when applicable. If interrupted, recover before retrying.

The managed instruction block preserves bytes outside its markers. Older unowned delivery blocks or conflicting workflow signatures need manual reconciliation. The installer does not silently rewrite unrelated instructions.

## Verification and context budgets

Installer development uses automated regression checks against temporary targets. Installation itself checks availability without running those tests or evaluating agents. Real task evaluations and token benchmarks remain optional and explicit. Automated routing checks inspect instruction contracts; they do not prove model compliance.

Current development evidence (2026-10-29): 104 automated tests passed, including temporary-target lifecycle, policy, migration, discovery-reporting, and static guidance checks. A live temporary project exercise downloaded and verified the pinned dependency, installed the payload, confirmed clean files and discovery of all 13 installed skills through Codex, upgraded, and uninstalled. This exercise called the installation routines directly; CLI policy behavior is covered by automated tests. Independent review found no actionable defects. Active MCP loading in a user's session, platform archives other than macOS ARM64, model compliance, and token savings remain unverified. No model task evaluation ran.

Installer structure assessment: version and source identity are in `scripts/framework_identity.py`, command parsing and dispatch are in `scripts/framework_cli.py`, pinned dependencies and their staged checks are in `scripts/framework_dependencies.py`, and transactional recovery and policy operations remain in `scripts/framework.py`. Removing recovery, conflict detection, dependency verification, or model compatibility checks would change documented safety or runtime behavior. This revision retains those capabilities; it does not claim an 80–90% reduction or a complete decomposition. Further extraction can be done without changing the lifecycle contract.

Maintainability budgets are 300 words for the managed instructions, 700 for delivery, 250 for each role entrypoint, 400 for each helper, and under 100 for routine communication rules. The specialized, explicitly invoked model-routing skill is exempt from the role-entrypoint budget.

Instruction size is not a measurement of tokens or subscription savings. Catalog metadata, task context, tool output, retries, and runtime behavior also affect usage. The static guidance checks enforce entrypoint word budgets, but do not measure task outcomes.

Manual acceptance: confirm the managed block occurs once, `status` reports clean files, the fresh session discovers framework skills, and its MCP server is active. An optional small authorized task can then check role/helper selection and review behavior. User performs applicable manual UX acceptance.

## Source and licensing

Framework skills and helpers are original concise adaptations. `sources.json` retains inspected revisions, licenses, and research purposes. `THIRD_PARTY_NOTICES` records attribution and limitations. Replaced upstream workflow skills are research references, not installation dependencies. The separately fetched Codebase Memory integration retains its upstream license and notices.
