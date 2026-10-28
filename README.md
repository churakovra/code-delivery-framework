# Code Delivery Framework (experimental)

A portable set of concise repository delivery instructions and task skills, plus a Python standard-library installer. The framework is experimental. Installation runs model routing to propose role assignments. Model evaluations remain manual and opt-in.

## Contents

- `AGENTS.md`: instructions for developing this framework.
- `templates/AGENTS.md`: consumer guidance inserted into a managed block.
- `skills/`: task-focused, model-neutral skills.
- `subskills.json`: pinned external skill and MCP dependencies and their role routing.
- `scripts/framework.py`: installer CLI (see below).
- `sources.json` and `THIRD_PARTY_NOTICES`: research provenance and attribution status.

## CLI

Use Python 3.11 or newer. The CLI is `python3.11 scripts/framework.py {install,upgrade,recover,status,uninstall,validate,select-models,apply-models,sync-models}`. Commands accept `--target PATH` (defaults to the current directory), `--global`, `--home PATH`, and `--codex PATH` (defaults to `codex`). Install, upgrade, and uninstall support `--dry-run`. Normal `validate`, `install`, and `upgrade` probe the Codex runtime and required models; `validate --offline` checks static inputs only. The dry run does not download dependencies or verify all conflicts or MCP activation. The installer records managed files and recovery information in `.codex/delivery-framework/`. This directory retains its existing name for compatibility with earlier installations. Framework skills are installed under `.agents/skills/code-delivery-framework/`; external subskills remain under `.agents/skills/`.

Install and upgrade fetch the pinned subskills, their supporting files, and the platform-specific Codebase Memory MCP release. This requires network access and Git; if a required dependency cannot be verified or obtained, the command reports a failure instead of claiming a complete install. The Web Design Guidelines subskill additionally fetches current guidelines when used. A clean installer status reports configured files and dependencies; it does not prove a Codex session has activated the MCP server.

Some environments resolve `python3` to an older interpreter. For example, in the development environment used to validate this bundle, `python3` is Python 3.9 and `python3.11` is provided through pyenv. There, run commands as `PYENV_VERSION=3.11.14 python3 ...` when the named `python3.11` shim is unavailable. In other environments, use any Python 3.11+ executable.

A non-dry-run installation invokes Codex with the model-routing skill and live web search before changing the target. This consumes the signed-in account's usage. The resulting choices are provisional: runtime availability is checked, but task quality and subscription consumption are not measured. If routing fails or selects an unavailable pair, installation stops before target changes. A dry run does not invoke model routing. The CLI returns a JSON welcome with the role assignments, available functions, and activation steps. It does not prove that the new Codex session loaded the skills or MCP server.

The framework selects an abstract role for each assignment. The role registry at `.codex/delivery-framework/roles.json` maps roles to required skills, role briefs, and policy keys. The installed `.codex/delivery-framework/model-policy.toml` maps those keys to models and reasoning efforts. Users or the model-routing skill can choose policy entries. Skills and roles are not one-to-one: select additional skills for the task as needed.

For delegated work, the delivery skill instructs the main agent to read the current registry and policy at launch. Where the runtime supports explicit model and effort overrides, it requests a generic subagent with those settings and supplies the role brief. Runtime support and agent compliance need a fresh-session check; an instruction does not guarantee execution. Fixed named roles remain a compatibility fallback. They cannot read policy changes at launch. If used, the active runtime settings must match the policy. A match on disk alone does not establish the active settings. After editing the policy, run `sync-models` to update these generated files, then restart Codex and verify the active role settings:

```sh
python3.11 scripts/framework.py sync-models --global --target "$HOME" --home "$HOME"
```

For a project installation, omit `--global` and use its project path as `--target`. The command checks model availability, refuses modified role files, and updates the manifest in a recoverable transaction. Upgrade stops on unsynchronized policy edits. Run `sync-models` before upgrade. Existing selection reports describe the earlier selection, not subsequent manual edits. `model-policy.md` is a fillable draft and does not control agent settings.

When the main agent does the work itself, it follows the role and applicable skills using the chat's current model. The policy cannot change an already-running agent's model. An unavailable model or unsupported override must be reported; the framework does not silently substitute a model.

To tailor model selection, provide a TOML profile with `--selection-profile PATH`. Include your plan, workload, priorities, and any preferred role assignments. Unspecified details are unknown. The profile is saved in the selection report, so do not include secrets. Without a profile, the installer cannot infer your plan or preferences. The bundled policy is not supplied as a candidate for a new installation.

After installation, review `.codex/delivery-framework/model-selection.json` for the provisional choices, rationale, alternatives, and source links. To deliberately reconsider an existing installation, create a proposal, review it, then apply it:

```sh
python3.11 scripts/framework.py select-models --target /path/to/project --selection-profile /path/to/profile.toml > proposal.json
python3.11 scripts/framework.py apply-models --target /path/to/project --proposal proposal.json
```

Use the same `--global`, `--home`, and `--target` values as the installation for global targets. `select-models` consumes account usage but does not change the target. `apply-models` validates the proposal against the current runtime and applies it in a recoverable transaction. Both stop on conflicts; do not overwrite user edits. Ordinary upgrade does not reselect. Existing installations retain any obsolete `demanding_implementation` entry until explicit reselection; it is not an active role.

Typical project-local sequence:

```sh
python3.11 scripts/framework.py validate --target /path/to/project --offline
python3.11 scripts/framework.py status --target /path/to/project
python3.11 scripts/framework.py install --target /path/to/project --dry-run
python3.11 scripts/framework.py install --target /path/to/project
```

For global use, pass `--global` and set `--target PATH` to the same canonical path supplied as `--home PATH`. When `--home` is omitted it defaults to the current process home. For example: `python3.11 scripts/framework.py install --global --target /Users/alex --home /Users/alex --dry-run`. Installing at the home path without `--global` is rejected. A project install manages `<target>/AGENTS.md`; a global install manages `<home>/.codex/AGENTS.md`. The installer does not create a branch, commit, pull request, release, or deployment.

To update an existing installation, use `upgrade` with the same `--target`, `--home`, and `--global` options used for its installation. `status` reports the recorded state; if a transaction was interrupted, run `recover` against the same target before retrying. `uninstall --dry-run` identifies preserved changes; uninstall leaves user-owned reused files and Codebase Memory indexes intact. Do not remove or overwrite modified user files to force an upgrade.

For example, update a global installation with:

```sh
python3.11 scripts/framework.py upgrade --global --target "$HOME" --home "$HOME"
```

The project MCP configuration is written under the project target; the global configuration is written under the configured home. Codex must trust a project before loading its project configuration. Restart Codex after installation or upgrade and verify the server in a fresh session. Discovery of framework skills in the nested directory also requires a fresh-session check; the installer tests do not establish it. This integration does not install hooks; other installed hooks may require separate trust through Codex.

## Migration and manual acceptance

The shared instruction block guides the main agent and delegated roles to communicate concisely while preserving necessary facts and evidence. The installer fetches the pinned `asd-ste100` skill and instructs all roles to apply it. The skill does not claim full ASD-STE100 dictionary compliance.

The installer adds a managed block to the project target's `AGENTS.md` or the global target's `.codex/AGENTS.md`, preserving bytes outside it. It does not automatically rewrite or reconcile older delivery instructions. If the target file already contains an older delivery-framework block or conflicting signature, inspect both sets of instructions and manually merge or remove the old block before installing; installation can stop on an unowned managed marker, and semantic conflicts require human reconciliation. Do not remove unrelated user-authored guidance.

After installation, confirm that the managed block appears once in `<target>/AGENTS.md` (project install) or `<home>/.codex/AGENTS.md` (global install), required files are reported clean by `status`, and a small authorized task loads the delivery skill from `<target>/.agents/skills/code-delivery-framework/delivery/SKILL.md`. For a global install, `<target>` is the configured home directory; no per-repository skill installation is needed. Check this with a repository that has no local delivery skill. Confirm the task follows the required review/check behavior and reports current evidence. User performs any requested UI acceptance; do not treat an installer check as UX acceptance.

## Verification status

A pre-review temporary project installation on macOS ARM64 installed all dependencies, reported 127 clean managed files, completed an MCP protocol initialization/tool check, and uninstalled. This historical exercise does not validate later edits. Other supported platform archives and a fresh-session Codex activation have not yet been exercised. Earlier installer tests and runtime checks predate dependency installation and are not evidence for the current implementation. A sandboxed runtime probe may be blocked during SQLite initialization by filesystem permissions; that is an environment limitation and does not establish that the runtime or models are unavailable. Use fresh validation and test results for the current state.

## Model evaluation

Model evaluations are optional development work and may consume tokens. The installer runs a model-routing recommendation but does not run comparative model evaluations. Validation does not run model routing or collect interaction traces. Evaluation prompts, results, and traces are kept locally under the ignored `evaluations/` directory and are not distributed with the framework.

## Source and licensing

Framework-authored skills are original concise adaptations of general workflow ideas; third-party subskills and MCP artifacts are fetched separately and are not bundled in this repository. Exact inspected revisions and known license information are recorded in `sources.json`. See `THIRD_PARTY_NOTICES` for attribution and known licensing limitations.
