# 05 — Installer v2.0: file ownership, lifecycle, upgrade, recovery

## 5.1 Why and scope

Existing v0.6 has ~1,475 lines across `framework.py`, `framework_cli.py`, `framework_dependencies.py`, `framework_identity.py` plus separate tests and release verifier. Its complexity comes from bundled skills, generated roles, model policy compatibility, Codebase Memory binary download/staged MCP verification, transactional installation, conflict protection, upgrade/recovery and runtime discovery. Preserve **safety**, remove **automatic external dependency orchestration** and redundant role generation.

**Chosen v2.0:** Python >=3.11 standard-library CLI with a small transaction core, static validators, structured status and safe lifecycle. No network and no LLM calls for core `install`, `upgrade`, `validate`, `status`, `uninstall`, `recover`, `doctor`. Do not set arbitrary source-line targets; correctness and auditability outrank “90% smaller.”

## 5.2 Install modes

### Core (default)

Inputs: packaged skill folders from the **approved** CDF 2.0 Skill Pack; managed AGENTS block; `cdf_reviewer.toml`, `cdf_diagnostician.toml` (optional but installed by default with core); `subskills.catalog.json` for future runtime discovery and optional integration metadata (not native loader).

Project target:

```text
<repo>/AGENTS.md                         # one owned managed block
<repo>/.agents/skills/cdf-*/...          # 12 core skills; optional extras described below
<repo>/.codex/agents/cdf_reviewer.toml
<repo>/.codex/agents/cdf_diagnostician.toml
<repo>/.codex/cdf/manifest.json          # state, hashes, provenance
<repo>/.codex/cdf/subskills.catalog.json # read-only metadata, no auto-install
```

Global target:

```text
<home>/.codex/AGENTS.md
<home>/.agents/skills/cdf-*/...
<home>/.codex/agents/cdf_reviewer.toml
<home>/.codex/agents/cdf_diagnostician.toml
<home>/.codex/cdf/{manifest.json,subskills.catalog.json}
```

**Packaging default:** install 12 delivery-relevant skills in core, **exclude** `cdf-explain` and `cdf-teach` unless `--with-learning`; include `cdf-model-calibration` as a manually invoked operator skill only if `--with-operator` (see the exact **12**-skill core list below). The exact v2.0 default list is:

`cdf-backend`, `cdf-code-review`, `cdf-codebase-research`, `cdf-debugging`, `cdf-documentation`, `cdf-frontend`, `cdf-implementation`, `cdf-orchestration`, `cdf-planning`, `cdf-requirements`, `cdf-ui-design`, `cdf-verification` — **12** core skills.

Operator extra: `cdf-model-calibration` (**1**). Learning extra: `cdf-explain`, `cdf-teach` (**2**). This totals **15** and is aligned with the companion Skill Pack. All references inside selected skills are installed with that skill. No installer-generic names conflict with community skills because primary names use `cdf-*`.

No `.codex/config.toml` modification by default, no `model-policy.toml` as an activated setting, no external Codebase Memory binary, no installation of community subskills, no branch/commit operations.

### Optional integration

`integrations list` and `integrations plan <id>` only print a provenance-pinned integration plan and permission/security checklist. They do not install. Initial v2.0 explicitly supports `codebase-memory-mcp` as informational/opt-in; an executable extended installer is not required for core release. If later added, it MUST be a separately permissioned module with trusted checksum, binary architecture validation and rollback. Community subskills are installed through their own supported mechanisms after review, never auto-updated because a CDF registry entry changed.

## 5.3 Exact CLI contract

Entrypoint: `python3 scripts/cdf.py` from the framework source checkout (a packaged console command may be added later but is not required).

```text
cdf.py validate [--offline] [--runtime] [--json]
cdf.py install --target PATH [--scope project|global] [--with-learning] [--with-operator] [--dry-run] [--json]
cdf.py upgrade --target PATH [--scope project|global] [--with-learning] [--with-operator] [--dry-run] [--json]
cdf.py status --target PATH [--scope project|global] [--json]
cdf.py uninstall --target PATH [--scope project|global] [--dry-run] [--json]
cdf.py recover --target PATH [--scope project|global] [--dry-run] [--json]
cdf.py doctor --target PATH [--scope project|global] [--json]
cdf.py integrations list [--json]
cdf.py integrations plan ID [--json]
cdf.py migrate-legacy --target PATH [--scope project|global] --dry-run [--json]
```

`--target` is a canonical target root; for `global`, it must be the selected home directory. Default scope is `project`. `validate` uses source bundle and **does not mutate target**. `--runtime` may probe known local Codex availability but must not call a task model. `--offline` is default behavior for source and basic runtime validation; a network action is never implicit. All mutating actions require `--target` to avoid accidentally writing into the wrong project. `--dry-run` executes every deterministic preflight possible without mutations.

For `upgrade`, extras selection is **retained from manifest if flags omitted**; providing `--with-*` adds an extra explicitly. To remove an extra, use a separate `upgrade --without-learning/--without-operator` if implemented; **for first v2.0 release, choose explicit `--without-learning` and `--without-operator` flags** and test both. Removing an extra follows normal managed-file conflict protection.

## 5.4 Manifest (single authority for ownership)

Schema in `schemas/manifest.schema.json`. Baseline fields:

```json
{
  "schema": 2,
  "framework_version": "2.0.0",
  "scope": "project",
  "source_revision": "<trusted Git SHA or package identifier>",
  "selected_extras": ["learning"],
  "state": "installed",
  "owned_files": {".agents/skills/cdf-backend/SKILL.md": {"sha256": "<64 hex>", "mode": 420}},
  "managed_blocks": {"AGENTS.md": {"start_marker": "<!-- BEGIN CDF 2.0 MANAGED: core -->", "end_marker": "<!-- END CDF 2.0 MANAGED: core -->", "sha256": "<sha256 of managed block>"}},
  "preserved_preimages": {"AGENTS.md": {"sha256": "<sha256 original bytes>", "backup": ".codex/cdf/backups/AGENTS.original"}},
  "transaction": null
}
```

Actual manifest must include source content digests and installed path map; no absolute personal usernames or secrets in tracked shared documents. Backups live in target's private management directory; file permissions preserved. Treat manifest as untrusted input: validate schema, prohibit `..` and escaping symlinks before any file operation; never follow untrusted backup paths.

`state` values: `installed`, `partial`, `recovery-required`, `conflict`; `absent` is a status output when no manifest exists, not an installed state. Recovery journal is authoritative over manifest state if both exist. Keep schema version separate from framework version.

## 5.5 Preflight and collision policy

1. Resolve/canonicalize target and install scope; reject nonexistent or unsafe target (project target must be a directory, preferably within a Git repo unless explicitly overridden). Reject root/system-home surprises.
2. Validate package skill directories/frontmatter, unique names, local references, JSON/TOML syntax, provenance. Test `cdf-*` name collisions in the scanned Codex locations; only owned same-name paths are eligible for update.
3. Build **entire** intended file map without modification. Exclude optional extras unless selected/retained.
4. Read existing managed manifest; reject schema/version mismatch unless explicit migration route.
5. Compare every owned file SHA with manifest. Any user edit to an owned file => conflict; never overwrite or auto-merge it. Show path and action to save/adopt outside CDF before retrying.
6. For AGENTS, accept exactly one intact previous managed block; preserve all bytes outside it (including CRLF where possible). If managed block changed or marker duplicated, reject with `conflict`. If no block exists, append safely without replacing user text. Detect legacy CDF block and demand legacy migration.
7. Reject symlinks at every target component, symlinked managed files, non-files, path traversal, and ambiguous path case collisions. Recheck immediately before mutation to mitigate concurrent edits. Do not claim perfect resistance to malicious concurrent filesystem races on unsupported OSes.
8. Return deterministic plan `add|update|delete|unchanged|conflict`; if any conflict, fail whole operation without partial updates.

Existing user-owned `.codex/config.toml` is never modified; even if it contains unrelated or legacy MCP settings, display a diagnostic only.

## 5.6 Transaction algorithm (installation/upgrade/uninstall)

A series of filesystem replacements is not truly atomic, so provide a crash-recoverable **journal**:

```text
plan = build_changes()
preflight_all_paths_and_expected_hashes(plan)
acquire_exclusive_cdf_lock(target)
recheck_expected_hashes_and_symlinks(plan)
create_private_transaction_dir()
write_preimage_backups_for_all_changed_paths()
fsync_backups_and_write_journal({old_hash,new_hash,mode,backup})
fsync_journal_and_dir()   # durable before first user-visible mutation
for each changed path in deterministic order:
    recheck current hash == expected_old_hash
    write temp in same directory, fsync, os.replace; preserve safe mode
commit_new_manifest_as_last_visible_write()
remove_journal_and_unlock()
```

For deletion: verify hash before unlink, record preimage; remove file only when manifest confirms ownership and bytes match expected. Non-empty user directories are never recursively deleted. Lock acquired via atomic directory creation; stale lock is diagnosed, not automatically stolen.

On ordinary exception: attempt `recover` immediately. On kill/power loss: next mutating command stops with `recovery-required`. `recover` compares each path to its **recorded old or planned new hash**; only revert a path if unchanged since the operation's known states. If external edit occurred after the journal, stop and preserve the path for manual reconciliation. Never overwrite changed files to force rollback. If recovery cannot be completed, state remains `partial`; status includes conflicting paths.

## 5.7 Upgrade rules

- Only schema 2 v2.0 installations use normal `upgrade`.
- Same target/scope and source provenance checked. Upgrade retains chosen extras by default.
- Role TOMLs, skill files and subskill registry are **managed files**. If locally modified, block and report differences; don't merge instructions automatically.
- User-controlled bytes outside `AGENTS` managed block are retained exactly.
- New skills added and retired ones removed only if owned and unchanged.
- If source revision marker is untrusted, label it provenance rather than authenticity. Installer must not treat a hash supplied by the same untrusted archive as independent verification.
- Successful copied files ≠ runtime discovery: `doctor` reports separate `filesystem`, `skills-discovery` and `agent-availability` statuses, with `unverified` when not probed.
- Never run model selection or agent task eval during upgrade.

## 5.8 Uninstall rules

For each owned file: if unchanged from manifest, delete; if changed, **preserve and list**. For AGENTS, remove exactly the intact managed block and preserve bytes outside it. Never delete user-created `AGENTS.md` merely because its managed block is removed. Remove CDF-created empty directories only. Do **not** remove third-party subskills, MCP binaries, indexes, user-managed `.codex/config.toml`, or old v0.6 files not owned by this manifest. Keep a partial manifest with preserved files if cleanup is incomplete. Re-running uninstall is safe and should complete when conflicts are resolved.

## 5.9 Legacy v0.6 migration behavior (explicitly manual for v2.0.0)

`migrate-legacy --dry-run` is a read-only **report**, not a hidden destructive upgrade. It detects v0.6 manifest/managed blocks, installed model policy, old generated agents, external MCP ownership and modified/reused files. Output an ordered recovery checklist and backup paths. First release does **not** auto-upgrade v0.6 installations.

Operator process:
1. Run old `status`, old `recover` if necessary; save current `AGENTS`, `.codex/config.toml`, model policy, user changes and manifest in private backup.
2. Run old `uninstall --dry-run`; inspect protected/modified files and external dependencies.
3. Use v0.6 uninstaller to remove only its owned unchanged files. Leave user-owned MCP/config/index intact; resolve any leftover managed block explicitly.
4. Run new v2.0 `install --dry-run`; inspect collisions and chosen scope.
5. Install core; run `status` and `doctor`; start a fresh trusted Codex session to verify discovery.
6. Restore **preferences**, not obsolete v0.6 role TOMLs, through the new advisory model policy after runtime checks.
7. If any step fails, stop, preserve backup, and restore through the version-appropriate recover/uninstall process. No blind file replacement.

This is slower once but substantially simpler and safer than an unverified automatic cross-architecture migration.

## 5.10 Status/doctor output contract

`status` is local and deterministic. `doctor` may probe installed Codex binary and parse diagnostic output without model work. Return:

```json
{
  "schema": 1,
  "state": "installed",
  "scope": "project",
  "files": "clean",
  "managed_block": "clean",
  "skills_discovery": "unverified",
  "native_agents": "unverified",
  "mcp": "not_managed",
  "issues": [],
  "next_action": "Start a new trusted Codex session and check skills and agents."
}
```

`clean` refers only to bytes and recorded state, not agent behavior. `unverified` must not be presented as `verified`. No user secrets or auth tokens in the JSON output.

## 5.11 Implementation component boundary (planned modules)

```text
scripts/cdf.py                   # CLI and stable JSON errors
cdf_installer/paths.py           # resolve, safe path, no symlinks
cdf_installer/bundle.py          # package/skill validation and selection
cdf_installer/planner.py         # pure desired file map and conflict diff
cdf_installer/journal.py         # fsync, backups, transactions, recover
cdf_installer/lifecycle.py       # install, upgrade, uninstall, status
cdf_installer/runtime_probe.py   # read-only Codex availability (optional)
cdf_installer/legacy.py          # v0.6 read-only migration report
```

No module should be large purely because it acts as a giant CLI function. Reuse v0.6 tests for known safety cases; don't copy duplicated legacy implementations. The exact file splits can be simplified further when a pure-function decomposition remains testable.

## 5.12 Required isolated lifecycle tests

`INSTALL-01`: fresh offline project → correct 12 core skills, 2 custom agents, manifest, one AGENTS block.  
`INSTALL-02`: global → correct home paths, no project files.  
`INSTALL-03`: user existing AGENTS with unusual whitespace/CRLF → outside block byte-identical after install/upgrade/uninstall.  
`INSTALL-04`: duplicate/modified CDF block → no mutation, conflict.  
`INSTALL-05`: managed file locally edited → no overwrite, conflict and explicit path.  
`INSTALL-06`: unrelated unowned skill file → preserved.  
`INSTALL-07`: external community same-name collision → fail/identify, never silently merge.  
`INSTALL-08`: symlink/`..`/malformed manifest → reject before mutation.  
`INSTALL-09`: injected failure after N file replacements → recover old bytes/modes.  
`INSTALL-10`: user edits file during failed transaction → preserve and mark partial.  
`INSTALL-11`: repeated install/upgrade/uninstall → deterministic state, no duplicate blocks.  
`INSTALL-12`: two processes contend → one acquires lock, other returns safe conflict.  
`INSTALL-13`: no network/model task invoked by install/validate/status.  
`INSTALL-14`: `--with-learning` adds only optional explain/teach, existing files remain clean.  
`INSTALL-15`: upgrade retains selected extras; `--without-learning` removes only unchanged owned files.  
`INSTALL-16`: old v0.6 manifest → normal upgrade refused, migrate dry-run lists steps.  
`INSTALL-17`: `status` distinguishes clean bytes vs unverified runtime discovery.  
`INSTALL-18`: binaries/MCP/indexes and user `.codex/config.toml` remain untouched by core and uninstall.  
`INSTALL-19`: no Git branch/index/commit changes.  
`INSTALL-20`: packaging validation rejects broken local references or duplicate primary skill names.
