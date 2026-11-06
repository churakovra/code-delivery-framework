# 09 — Concrete interfaces, CLI error contracts and adapter boundaries

This appendix eliminates residual implementation ambiguity by specifying the **internal contracts** for the small Python installer and the **non-enforcement** role of CDF's runtime guidance. It does not require implementing a new LLM orchestration engine.

## 9.1 Module interfaces (Python 3.11+)

Suggested typed dataclasses and functions; module placement can change without altering public behavior:

```python
@dataclass(frozen=True)
class InstallRequest:
    action: Literal['install', 'upgrade', 'uninstall', 'recover', 'status', 'doctor']
    scope: Literal['project', 'global']
    target: Path
    extra_learning: Literal['retain', 'enable', 'disable'] = 'retain'
    extra_operator: Literal['retain', 'enable', 'disable'] = 'retain'
    dry_run: bool = False

@dataclass(frozen=True)
class FileAction:
    relative_path: str
    operation: Literal['add', 'update', 'remove', 'unchanged']
    expected_before_sha256: str | None
    after_sha256: str | None
    mode: int | None

@dataclass(frozen=True)
class ChangePlan:
    actions: tuple[FileAction, ...]
    managed_block_operation: Literal['append','replace','remove','unchanged','none']
    conflicts: tuple[str, ...]
    scope: str
    target: Path

# Pure/preflight steps; no side effects.
def build_bundle(source_root: Path, extras: set[str]) -> dict[str, bytes]: ...
def plan_changes(request: InstallRequest, bundle: dict[str, bytes], manifest: dict | None) -> ChangePlan: ...
def check_plan_paths(request: InstallRequest, plan: ChangePlan) -> None: ...

# Mutating steps; require preflight and exclusive lock.
def apply_change_plan(request: InstallRequest, plan: ChangePlan) -> dict: ...
def recover_transaction(request: InstallRequest) -> dict: ...

# Read-only diagnostics.
def inspect_status(request: InstallRequest) -> dict: ...
def probe_runtime(request: InstallRequest) -> dict: ...
def inspect_legacy(request: InstallRequest) -> dict: ...
```

Do not make tasks depend on these exact names if a simpler implementation is demonstrably clearer, but preserve the contracts: pure plan; side effects behind apply/recover; status doesn't mutate; no network during core execution.

## 9.2 Stable response envelopes and exit codes

Machine-readable stdout returns **one JSON object** for each CLI invocation. Human-readable mode may format it but must not interleave progress text with JSON. Errors are returned as a JSON object with `state="error"`, `code`, `message`, `affected_paths` (if any), and `next_action`. No secrets or environment credentials in errors.

Exit codes:

| Exit | Semantics |
|---|---|
| 0 | Successful action or clean read-only report; `--dry-run` ready |
| 2 | Invalid input/manifest, collision, unsupported upgrade or validation failure |
| 3 | Interrupted transaction / recovery required / cannot safely recover |
| 4 | Optional runtime probe unavailable (only for strict `validate --runtime`; normal `doctor` reports `unverified` without nonzero exit) |
| 5 | Unexpected filesystem/system I/O failure |

**Error codes:** `INVALID_REQUEST`, `INVALID_BUNDLE`, `UNSAFE_TARGET`, `PATH_COLLISION`, `MANAGED_FILE_MODIFIED`, `MANAGED_BLOCK_MODIFIED`, `MANIFEST_UNSUPPORTED`, `LEGACY_MIGRATION_REQUIRED`, `RECOVERY_REQUIRED`, `CONCURRENT_MUTATION`, `RUNTIME_UNAVAILABLE`, `IO_FAILURE`.

For `install` on an already installed same version, return `PATH_COLLISION` with guidance to use upgrade; do not pretend it is a new install. For `uninstall` with no installation, return `state="absent"` and exit 0. For `upgrade` with no matching schema-2 installation, return `MANIFEST_UNSUPPORTED` or `LEGACY_MIGRATION_REQUIRED` according to detection.

`--dry-run` returns `state="ready"` or `state="conflict"`, `planned_actions` and a warning that actual apply re-checks current hashes. It never downloads or executes commands, regardless of whether runtime is installed. Absolute target path in local JSON response is acceptable; do not write it into a source-controlled report by default.

## 9.3 AGENTS marker exact contract

Core block markers are exactly:

```text
<!-- BEGIN CDF 2.0 MANAGED: core -->
<!-- END CDF 2.0 MANAGED: core -->
```

- The installer uses the template bytes between these markers and includes markers in the block hash. Preserve original outside bytes including line endings and all unrelated text.
- If `AGENTS.md` did not exist, create it containing only the block plus a final newline; on uninstall remove it only if no content remains and the installer owns the file.
- If existing file is nonempty and lacks a trailing newline, insert exactly one newline before the managed block; store the preimage so uninstall can reconstruct original bytes exactly when outside text is unchanged.
- If an existing block appears once and is intact, replace/remove it at the exact original byte interval. If multiple blocks or user edits to the block, conflict without mutation.
- After uninstall, if the user altered text outside the block, remove only the intact block and keep their edits; don't restore a stale entire AGENTS backup over newer user content.

## 9.4 Transaction journal exact minimum

`schemas/transaction-journal.schema.json` defines core fields. Journal is persisted before any target changes and includes `transaction_id`, `action`, `target_canonical`, `scope`, `phase`, `paths` with preimage/new hashes and backup names, and manifest planned hash. `phase` is `prepared|applying|complete` but the recovery algorithm never trusts phase alone: it checks actual bytes per path.

- Journal backup bytes are copied into private managed transaction directory with mode 0600 where supported; directory must not be world-readable.
- A delete/mode-only operation still records file state.
- The manifest file is replaced after all other changes, so any crash without journal cleanup is recoverable.
- Successful commit removes journal last; orphaned journal makes status `recovery-required` even if files appear complete, until recover reconciles them.
- Files modified concurrently after journaling are preserved; recovery may be incomplete and needs operator reconciliation.

## 9.5 Skill discovery capability and TOML adapter

The installer writes source files but never assumes a given Codex build has loaded them. The `runtime_probe` must distinguish:

- `binary_available`: Codex executable resolved (or absent).
- `version_observed`: exact version string, not an invented minimum.
- `agent_schema_supported`: can parse sample native agent TOML according to current docs, or `unverified`.
- `skill_catalog_detected`: actual discovered skill names and paths where a supported read-only endpoint provides them; else `unverified`.
- `active_model_observed`: only from supported runtime session evidence, never from disk files.
- `mcp_active`: not managed; report `not_managed` or `unverified`, not `success`.

Avoid brittle parsing of private/experimental JSON. If a `codex debug` command exists, require explicit opt-in for probing experimental output and guard errors. A clean file install is success for installer contract but **not proof of active skill selection**.

## 9.6 Adapter model selection contract

```python
@dataclass(frozen=True)
class ModelResolution:
    role: str
    tier: str
    candidate_model: str | None
    candidate_effort: str | None
    requested_model: str | None
    requested_effort: str | None
    observed_model: str | None
    observed_effort: str | None
    state: Literal['confirmed','requested_unconfirmed','fallback','unavailable']
```

This is a **telemetry and advisory** structure. The root CDF skill reads policy and may propose a child setting through runtime support. It is not an API wrapper required for all tasks. Never write a fake resolved model into an agent file. If a mandatory independent reviewer is unavailable, review gate blocks even if the model policy would like to use a different fallback.

## 9.7 Regression tests for interfaces

`CONTRACT-01`: exact block marker matching, missing/multiple/modified marker cases and CRLF.  
`CONTRACT-02`: deterministic `plan_changes` sort and no file writes.  
`CONTRACT-03`: JSON stdout exactly one parseable object in `--json`, stable error codes/exits.  
`CONTRACT-04`: manifest and journal schemas validated before path operations.  
`CONTRACT-05`: unknown runtime output gives unverified, never confirmed.  
`CONTRACT-06`: extras retention/enabling/disabling deterministic; 12 core installed by default, 15 with all extras.  
`CONTRACT-07`: model resolution states distinguish requested/observed and prohibit false substitution.  
`CONTRACT-08`: legacy marker detection does not delete or overwrite CDF 0.6 installations.


## 9.8 Implemented interface clarifications and limits

This appendix records design intent; the current CLI and implementation are authoritative where they differ. Mutating operations require POSIX and fail early on unsupported platforms. Installer private-state exclusions are a managed additive block in `<target>/.codex/.gitignore`; cleanup intent is `<target>/.codex/cdf-cleanup.json`, with recovery support for the legacy root `.cdf-cleanup.json`. Uninstall converges when owned paths are already missing. `uninstall --release-modified-skills` preserves an entire modified skill while releasing CDF ownership. It preserves AGENTS content and backup. The installer never untracks files or changes the Git index; tracked-secret remediation is manual.

Evaluation execution requires both `--allow-model-runs` and `--trusted-local-execution`. Trusted-local execution is not an OS sandbox and applies to adapter and fixture code; no verified sandbox provider ships. Preflight is read-only and does not execute the adapter or validate live Codex version/resume compatibility. `standardized` comparison is the default and requires equal attested tools. `installed-system` allows attested tool differences, is descriptive, and remains blocked until actual installed-system setup evidence is supplied. Run and grading manifests test hash consistency, not authenticity; usage is re-derived from retained trace data. No live G01/G02/G09/G13 acceptance or savings measurement is claimed.
