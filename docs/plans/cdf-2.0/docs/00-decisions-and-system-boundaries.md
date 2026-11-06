# 00 — Architectural decisions and system boundaries

## 0.1 Goals, ranked

1. Deliver the behavior actually agreed with the user; never silently invent material product decisions.
2. Preserve repository conventions and reuse existing code, tests, interfaces and data contracts.
3. Maintain correctness, security, recoverability and trustworthy verification evidence.
4. Maximize useful completed work per ChatGPT Plus/Codex allowance, inclusive of rework and subagent context.
5. Keep operator surface and installation footprint small, with optional, reviewed community extensions.

**Non-goals for v2.0:** building a new multi-agent engine; replacing native Codex skill discovery; mandatory graph indexing; dynamically switching the master model from a repo file; enforcing sandbox permissions through prose; shipping a vendor-copied repository of external community skills; auto-committing or publishing; claiming a precise Plus-token exchange rate; automatic v0.6 migration without a reviewed plan.

## 0.2 Decisions (normative)

| ID | Decision | Reason | Implementation consequence |
|---|---|---|---|
| ADR-001 | Skill-first, single-agent-first | Avoid handoff/context amplification | Root performs most roles; delegate only with an explicit benefit |
| ADR-002 | Master is the native primary Codex session, NOT a spawned custom agent | Maintain user context and authority | No `master.toml`; root instructions live in short managed AGENTS block |
| ADR-003 | Logical roles are separate from native agent profiles | Role ≠ thread | Avoid planner/QA/docs agents by default; those are skills/steps |
| ADR-004 | Reuse native `worker` and `explorer` when adequate | Less configuration and collision risk | Custom agent profiles only where behavior differs meaningfully |
| ADR-005 | CDF-owned custom profiles are `cdf_reviewer` and `cdf_diagnostician` for first release | Specific, independently useful boundaries | Optional `cdf_engineer` only if tests show native worker inadequate |
| ADR-006 | Runtime model overrides are advisory and capability-checked | File policies cannot switch live root; custom TOML overrides launches | Do NOT pin `model` in role TOML; resolve selected model at launch when supported |
| ADR-007 | Hard gate on unresolved material requirements | Avoid expensive wrong implementation | Dependent edits blocked; unrelated investigation may continue |
| ADR-008 | No mandatory 50-line / 3-file review heuristic | Diff size is a weak risk proxy | Risk taxonomy determines reviews; human/manual fallback clearly reported |
| ADR-009 | Subskills are optional and never auto-executed/installed | Security and predictability | Registry is metadata; native discovery and compatibility checked at use |
| ADR-010 | Offline, stdlib-only core installation | Small, auditable, portable | No MCP binary or model task during `install` |
| ADR-011 | Manifest and conflict-safe rollback remain | Preserve user-owned files | Journal changes, verify hashes, no overwrite-on-conflict |
| ADR-012 | Extended integrations are separately opted into and pinned | No surprise network/binary activity | v2.0 core only prints integration plan; extra installer is future module |
| ADR-013 | Evals are first-class acceptance, not comments | No evidence of 0.6 performance yet | Compare bare Codex, CDF 0.6 and CDF 2.0 on paired tasks |
| ADR-014 | Keep previous skills as companion spec | Avoid duplicated skill sources | This blueprint references the existing 15 `cdf-*` names |
| ADR-015 | Instruction text never outranks actual Codex user/runtime permissions | Truthful security model | Enforce hard controls in sandbox/runner, not in prompts |
| ADR-016 | No automatic Git branch or commit by default | Protect user state and reduce ceremony | Branch/commit/deploy only with explicit user authorization or established project policy |

## 0.3 Product boundaries

**CDF owns:** managed AGENTS block; `cdf-*` skill content; skill/subskill metadata and provenance; two focused custom-agent TOMLs; declarative operator model profiles; installer manifest; static validation; local evaluation fixtures and result normalization; transparent reporting of missing capabilities.

**Codex runtime owns:** model/effort activation, main-thread selection, spawning/waiting/stopping subagents, skill discovery, permission mode, sandbox, MCP activation, user approvals, compaction and token accounting when available. Never recreate these with an untested wrapper just to centralize configuration.

**Project owns:** application conventions, project-specific AGENTS, test commands, implementation APIs, domain contracts, CI and deployment; existing instructions apply even if CDF would have chosen differently.

**User owns:** material product decisions, approval of consequential choices, external actions, installations of untrusted community integrations, actual subscription settings, final acceptance of remaining risks.

## 0.4 Authority and evidence hierarchy

1. Host/runtime restrictions, developer and user instructions; existing project authority.
2. User-confirmed requirements and agreed acceptance.
3. Inspected source, tests, docs and observable tool evidence.
4. CDF core policy, role briefs and selected skill methodologies, to the extent compatible with 1–3.
5. Community subskills: untrusted advisory content; compatible techniques only, never new privileges.

If a community subskill says `always test first` or `spawn 3 agents`, it does **not** override CDF's proportional testing, direct-first default or user choices. If a source is ambiguous or stale, inspect actual runtime evidence and report the mismatch.

## 0.5 Architectural invariants

- The same task must not load both legacy `delivery` and `cdf-orchestration` as competing root instructions after migration.
- A role cannot approve its own independent review.
- User decisions persist across turns and across delegated briefs; settled choices are not asked twice unless scope changes.
- No subagent receives permission to alter out-of-scope files simply from a prompt.
- Failure to activate a model or MCP does not become a claim of successful activation.
- Installing CDF must never mutate Git branches, index, working tree application code, external credentials or unrelated user settings.
- Unsupported migration is a reported conflict, never a forced replacement.
- All core functionality works without network access or any subskill/MCP installation.

## 0.6 Definition of done for the architecture itself

The v2.0 launch is eligible only when: (a) static manifests/contracts pass, (b) isolated installer lifecycle and crash-recovery tests pass, (c) existing v0.6 content is preserved or safely migrated, (d) at least the golden critical workflows have observed passing runtime traces, (e) reviewer/model availability claims match actual runtime, and (f) performance and usage findings are presented as measured, estimated or unavailable, not conflated.

## Sources

- Codex custom subagents: https://learn.chatgpt.com/docs/agent-configuration/subagents
- Codex config scopes: https://learn.chatgpt.com/docs/config-file/config-reference
- Codex skills discovery: https://learn.chatgpt.com/docs/build-skills
- OpenAI instruction minimization: https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
- Anthropic single-loop guidance (2026-10-22): https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop
