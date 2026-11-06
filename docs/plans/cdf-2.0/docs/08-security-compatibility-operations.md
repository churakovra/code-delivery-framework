# 08 — Security, threat model, compatibility and operations

## 8.1 Trust surfaces

**Untrusted inputs:** user task text, repository README/issues/comments, downloaded community SKILL.md and scripts, tool/MCP output, remote source archives, Git branch/commit metadata, installer manifest and resolved local paths. A lower-trust skill cannot authorize permission escalation, filesystem deletion, network exfiltration, credential access, role-policy replacement or unrequested tool execution.

**Permission enforcement:** only Codex's actual sandbox and approval mechanisms constrain tool actions. A custom-agent TOML `read_only` prose restriction is advisory. In the reference setup, the child inherits parent sandbox/permissions and MCP access. Use an actually separate read-only session/workspace when independent security isolation is necessary. Do not describe a successful subagent review as proof it could not have edited files unless the runner enforced that.

## 8.2 Community subskill threat model

Risk categories: prompt injection ("ignore host instructions"), unexpected shell scripts, network fetch, secrets enumeration, stale/compromised upstream revision, license violation, skill-name collision, incompatible tool invocation (Claude-specific tools in Codex), excessive implicit activation and context flooding.

Admission checklist:
1. Candidate has exact repository/revision, file path, author/license note and inspected origin in `subskills.catalog.json`.
2. Confirm installed native skill name, version and actual tool availability; registry presence alone is not installation.
3. Read entrypoint and any scripts/tool declarations; don't run unreviewed commands automatically.
4. Determine activation trigger, excluded cases, local CDF fallback and whether optional instructions contradict host permissions or accepted behavior.
5. Never auto-download, auto-update or enable a subskill during normal coding or core install.
6. On material capability gap, disclose unavailable specialist and proceed with local CDF skill when safe; if review/security gate truly requires independent capability, block that gate.
7. When upgrading a pinned SHA, treat it as a new external artifact requiring provenance, license and regression review.

License handling: MIT and Apache-2.0 skills may permit reuse with obligations, but CDF 2.0 should **link rather than vendor** full third-party source by default. Some candidates have per-skill exceptions or non-permissive licensing. Do not rely on the repository root license for every file; check the exact asset. Track attribution of ideas, and include notices only where content actually redistributed.

## 8.3 Supply chain and archive verification

When distributing CDF release archives, use trustworthy release provenance and an independently obtained trusted SHA-256 or signed release. `SOURCE_REVISION` inside the archive is provenance, not independent authentication. Validate ZIP/TAR extraction against traversal/symlinks, limits and malicious files. Core release can be distributed as Git checkout or verified package; installer must not fetch third-party binaries.

For future extended MCP installer, pin version, platform archive checksum and executable compatibility; stage and probe before mutation; never treat successful local binary execution as activation in a user's already-running Codex session.

## 8.4 Filesystem and installer safety

- Canonical target root, refuse `..`, symlink escapes and unexpected special files. Do not install to filesystem root.
- All core commands except explicit install/upgrade/uninstall/recover are read-only; `--dry-run` does not modify anything.
- Manifest hashes protect ownership. Modified managed files cannot be silently overwritten.
- Use preimage journal/atomic replacements; run crash/failure-injection tests and respect concurrent modifications.
- `AGENTS.md` is treated as user-owned outside a marked block; after uninstall return its other bytes unchanged.
- Never touch arbitrary `.codex/config.toml`, credentials, third-party skill trees or MCP indexes.
- In shared/global scope, preserve private file modes and exclude secret content from logs.

## 8.5 Behavior safety and data fidelity

Requirements: no guessed material decisions; user-selected error semantics or data behavior cannot be overwritten by a "best practice". Implementation: source reuse and project conventions first; no generalized architecture rewriting without actual need. Verification: actual raw evidence and test revision, no claims from outdated test results; high-risk independent review remains blocked if unavailable. Git and external actions require user authorization or project policy. These remain true even if an optional subskill prescribes more aggressive behavior.

## 8.6 Codex version compatibility gate

Supported target: Codex CLI/app server where native skills discovery and custom-agent files work. Exact version minimum should not be fabricated; store observed `codex --version` and feature probe results. If a feature isn't supported, degrade to direct work or explicit role brief if it preserves required behavior. A missing optional ability cannot bypass mandatory high-risk independent review.

Project `.codex/config.toml` is loaded only for trusted projects, and user/global/profile config scope differs; CDF never writes profile selection into a project config. Native `worker` and `explorer` may differ across versions: test actual availability. `cdf_reviewer` and `cdf_diagnostician` files are approved custom profiles only when recognized by runtime.

## 8.7 Operator commands and failure playbook

**After installation:**

```sh
python3 scripts/cdf.py status --target /path/to/repo --scope project --json
python3 scripts/cdf.py doctor --target /path/to/repo --scope project --json
```

Status `files=clean`, `skills_discovery=unverified` is **not** full active proof: restart/start a fresh trusted Codex session and inspect skill/agent catalog; perform a bounded task if authorized. For suspected stale global install, inspect `~/.agents/skills` and `~/.codex/AGENTS.md` but do not mutate them silently.

**Crash recovery:** if status says recovery required, stop upgrades; inspect journal and run `recover --dry-run` then `recover`; if conflicts remain, preserve files and user edits, resolve manually and retry. Never `rm -rf .codex` or reset the Git tree as an install workaround.

**Unexpected behavior:** compare current loaded AGENTS/skills and actual configured role from runtime, not simply source tree. Check whether the global older CDF 0.6 remains installed and its `delivery` instructions still load. Do not infer that editing workspace files changed the live global installation.

**Cost anomaly:** check actual loaded skill descriptions/bodies, multiagent spawn trace, repeated codebase reads, retries and time spent waiting on tools. No unsupported token savings estimate from file byte size.

**Model mismatch:** inspect root/current settings and custom agent TOML, then logged requested/observed pair. Do not silently rewrite user's global configuration.

## 8.8 Release checklist

- [ ] Skill Pack names, refs and subskill ownership validated; license/provenance notes reviewed.
- [ ] Fresh core install from isolated source with network unavailable.
- [ ] Project and temporary global installation, status, upgrade, uninstall, recover tested.
- [ ] User-owned AGENTS bytes outside managed block preserved in all paths.
- [ ] Fresh trusted Codex session discovers selected skills/custom profiles (or explicitly marked unverified).
- [ ] Requirements gate and high-risk review negative scenarios observed.
- [ ] No model/effort or MCP activation claims without runtime evidence.
- [ ] No credentials/user home mutation by test harness.
- [ ] Source and release provenance independently verified when distributing archive.
- [ ] Release notes distinguish untested platform/model combinations and Plus usage uncertainty.
