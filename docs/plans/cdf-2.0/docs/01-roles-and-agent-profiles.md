# 01 — Roles, native agent profiles and skill composition

## 1.1 Key decision

A **role** is a reusable responsibility contract. A **subagent** is an optional runtime thread. The root master can apply Engineer, Explorer, Planning, QA and Documentation competencies without spawning anything. Primary `cdf-*` skills are the procedures that fill those competencies; a role profile must NOT copy their complete text.

Codex currently supplies built-in `default`, `worker` and `explorer` agents. `~/.codex/agents/*.toml` and `<repo>/.codex/agents/*.toml` define optional custom agents with `name`, `description` and `developer_instructions`. A custom profile's `model` and `model_reasoning_effort` take precedence over a requested spawn setting. Custom files cannot override inherited sandbox, approvals, provider or MCP permissions. Thus avoid custom profiles without a unique purpose. Reference: https://learn.chatgpt.com/docs/agent-configuration/subagents.

## 1.2 Logical roles and deployment mapping

| Logical role | Responsible for | Master can perform? | Runtime mapping | Long-lived config? |
|---|---|---|---|---|
| MASTER | User clarification, scope ownership, risk, orchestration, integration, final statement | Root only | Native primary session + short managed AGENTS block | No `master` agent file |
| ENGINEER | Approved changes, local tests, minimal docs, direct bug fixes | Yes, default | Root; delegated native `worker` when worthwhile | No custom file initially |
| EXPLORER | Narrow repository evidence/impact tracing | Yes | Root or native `explorer` for disposable context | No custom file initially |
| REVIEWER | Independent inspection of actual patch, contracts, failure paths | No, if **independent review** required | `cdf_reviewer` custom subagent | Yes |
| DIAGNOSTICIAN | Discriminating hypotheses for repeated/complex failures | Yes for first attempt; independent variant only if needed | `cdf_diagnostician` custom subagent | Yes |
| UI DESIGNER | Consequential interface direction and visual verification | Yes | Engineer + `cdf-ui-design` skill | No custom file by default |
| PLANNER / QA / DOCUMENTATION | Phases, not stable agent identities | Yes | `cdf-planning`, `cdf-verification`, `cdf-documentation` | No |

Do not install a catch-all `specialist` agent: expertise is in the relevant skill/subskill, not the label. A concrete specialised custom agent may be added later only with measurable evidence that the ordinary role+skill combination is inadequate.

## 1.3 Per-role responsibilities, exclusions and evidence

### MASTER (root)

**Must:** establish intent and material decisions; check relevant source; hold baseline and acceptance; choose direct vs delegate; coordinate ownership; integrate changes; ensure checks; disclose blockers and actual review. **May:** implement directly, ask user questions, plan, research, trigger subagents where permitted. **Must not:** treat own self-review as independent; assume selected model changed because file changed; silently decide material behavior; create unrequested documents/commits.

Primary skills: `cdf-orchestration` for substantial delivery, `cdf-requirements` for unresolved material behavior, `cdf-planning` for cross-component work, `cdf-codebase-research` for unknown structure, `cdf-implementation` and domain skills for direct execution, `cdf-verification` for actual evidence. Optional: `cdf-model-calibration` only when user explicitly requests model policy research; `cdf-explain`/`cdf-teach` on explicit learning requests.

### ENGINEER

**Input:** accepted behavior; restricted file/module ownership; baseline; expected checks; dependencies and shared contracts. **Must:** read relevant existing code and callers; reuse patterns; implement minimal change; add meaningful focused regression; return changed paths, checks and uncertainties. **Must not:** reinterpret material decisions, write outside ownership, manage Git/PR/deploy, spawn children. If a material question emerges, return `BLOCKED_NEEDS_DECISION` to master.

Primary skills: `cdf-implementation`; conditional `cdf-backend`, `cdf-frontend`, `cdf-debugging`, `cdf-verification`, `cdf-documentation`, `cdf-ui-design`; `cdf-codebase-research` only if structure unclear.

### EXPLORER

**Input:** concrete question, source root, bounded search area, existing findings, coverage/freshness status. **Must:** cite concrete files/symbols, distinguish code facts from inference, return relevant relationships, unknowns and source freshness. **Must not:** edit files, present graph absence as proof of no usages, repeat broad searches already supplied, spawn children. The no-edit rule is *advisory* unless reviewer runs in an actually read-only sandbox.

Primary skill: `cdf-codebase-research`. Community Codebase Memory integration optional, not required.

### REVIEWER

**Input:** actual diff/baseline, accepted behavior, scope, commands and fresh outputs (not implementer summaries alone). **Must:** inspect full relevant diff and impacted callers, consider failure paths and security/concurrency/data effects, return prioritized findings or an explicit no-findings result with inspected scope. **Must not:** edit the implementation, rubber-stamp a summary, invent failures, automatically expand scope. A fix is implemented by engineer; a substantive fix must be reviewed again.

Primary skill: `cdf-code-review`; conditional `cdf-verification` for evidence scrutiny, `cdf-backend`/`cdf-frontend` for actual domain review. A reviewer must not consume a second unrelated full quality plan when the diff is low-risk.

### DIAGNOSTICIAN

**Input:** repeated failure, logs/reproducer, failed approaches and hypotheses, test/environment baseline. **Must:** identify multiple plausible causes, find the minimum discriminating experiment, predict evidence, report confidence and precise next action. **Must not:** fix code or repeatedly rerun the same failing test unless explicitly reassigned by master. When unavailable, master runs the local `cdf-debugging` hypothesis method and truthfully reports independent diagnosis unavailable.

Primary skill: `cdf-debugging`; conditional `cdf-codebase-research`, `cdf-backend`/`cdf-frontend`.

## 1.4 Composition matrix

Legend: `R` role requires skill **for that kind of assignment**, `C` conditional, `—` not activated by role alone. The matrix is routing guidance, **not** an instruction to read every listed skill at thread creation.

| Skill | MASTER | ENGINEER | EXPLORER | REVIEWER | DIAGNOSTICIAN |
|---|---|---|---|---|---|
| cdf-orchestration | R for delivery | — | — | — | — |
| cdf-requirements | R if unresolved | report gaps | — | check against accepted brief | — |
| cdf-planning | C substantial | C complex | — | — | — |
| cdf-codebase-research | C | C | R | C | C |
| cdf-implementation | C direct edit | R | — | — | — |
| cdf-backend | C backend | C backend | — | C domain | C |
| cdf-frontend | C UI | C UI | — | C domain | C |
| cdf-ui-design | C redesign | C redesign | — | C design review | — |
| cdf-debugging | C failure | C failure | — | — | R |
| cdf-code-review | C self-check *not independent* | — | — | R | — |
| cdf-verification | R when modified | C | — | C | C verify claim |
| cdf-documentation | C necessary changes | C | — | C docs regression | — |
| cdf-model-calibration | explicit only | — | — | — | — |
| cdf-explain, cdf-teach | explicit only | — | — | — | — |

Subskill activation follows the **owner primary skill's** catalog triggers. Roles do not force external subskill loading. De-duplicate similar resources; if two primary skills suggest the same candidate, read its body once and reuse current-context evidence.

## 1.5 Custom TOML profiles (exact v2.0 draft)

`templates/cdf_reviewer.toml` and `templates/cdf_diagnostician.toml` are directly installable custom-agent files after version compatibility is checked. The stable `name` values are `cdf_reviewer` and `cdf_diagnostician`, avoiding collisions with native `explorer`/`worker` and legacy `delivery-*`.

Do **not** include `model`/`model_reasoning_effort` in these files. Effective settings are supplied on spawn where supported, else inherited from runtime or selected default. If per-spawn overrides aren't supported, do not claim the policy was applied. The installer never silently substitutes a different fixed model.

Note: Codex `read-only` is NOT guaranteed by `developer_instructions`. For strict isolation (security audit, untrusted code or external commands), create a separately configured read-only session/runner. In a normal shared parent session, the restriction is an expectation and violations must be detected via diff/trace.

## 1.6 Delegated role selection algorithm

1. Keep work in root unless `delegation-criteria.md` (see 03) justifies a subagent.
2. Match responsibility: implementation → built-in `worker`; mapping → built-in `explorer`; independent diff → `cdf_reviewer`; multi-hypothesis diagnosis → `cdf_diagnostician`.
3. Detect available agent type from actual runtime. If unavailable, generic agent with an explicit role brief is allowed only when it preserves a necessary property and does not invent new capabilities.
4. Apply model policy only via supported spawn or root settings. Custom agent TOML does not pin a model.
5. Pass compact task-specific handoff, **not** global instructions in full. Trust only actual role availability and permissions.
6. On return, verify changed paths, assertions and citations; responsibility returns to root.

## 1.7 Migration from old roles.json

| Existing role | New owner | Migration outcome |
|---|---|---|
| planner | Root `cdf-planning` | Remove native planner profile |
| implementation | Root/worker `cdf-implementation` + domain | Use native `worker`; no static engineer TOML |
| designer | Root/engineer `cdf-ui-design` | Remove default design agent; optional future specialization |
| qa | Root `cdf-verification` | Remove independent QA agent by default; proof comes from tools |
| reviewer | Custom `cdf_reviewer` | Preserve actual diff and independence semantics |
| documentation | Root/engineer `cdf-documentation` | Remove default docs agent |
| diagnosis | Custom `cdf_diagnostician` | Preserve independent multi-cause diagnosis |

Old `roles.json` is kept only by legacy installer until migration is complete; v2.0 core does not make it a second source of runtime truth. The skill manifest and native TOML are the only installable role artifacts.

## 1.8 Role acceptance tests

- `ROLE-01`: trivial edit → root, no new thread, correct domain skill.
- `ROLE-02`: backend API edit delegated → built-in worker if runtime supports and benefit evident; required acceptance supplied, no child delegation.
- `ROLE-03`: independent review → reviewer gets diff and raw tests; no writes; reviewer checks at least one affected caller.
- `ROLE-04`: unavailable reviewer → high-risk task marked review blocked; root self-review never described as independent.
- `ROLE-05`: old planner/QA/docs agent files not installed in a fresh v2 target.
- `ROLE-06`: source model overrides not in custom TOML; explicit spawn wins where supported; unknown runtime reported.
- `ROLE-07`: runtime permissions inherited, and read-only profile claims remain advisory unless isolated.
