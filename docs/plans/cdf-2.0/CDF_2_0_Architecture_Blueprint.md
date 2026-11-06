# CDF 2.0 — Complete Architecture & Implementation Blueprint

> Дата: 5 ноября 2026. Baseline: `churakovra/code-delivery-framework` v0.6.0, `3ff534627e8b10de3dba2c6443855e870567ef84`.
>
> Этот документ описывает **все части плана за исключением полного текста новых skills**. Для skills использовать связанный документ `CDF_2_0_SKILL_SPEC.md` и `CDF_2_0_Skill_Pack`. Ниже — проектные решения, роли, рабочий цикл, делегация, model routing, installer, безопасность, тесты и дорожная карта.
>
> Статус: план и примерные контракты. Не выполнена реализация в GitHub и не выполнены runtime agent evaluations.

## Навигация

- [00-decisions-and-system-boundaries.md](#00-decisions-and-system-boundaries)
- [01-roles-and-agent-profiles.md](#01-roles-and-agent-profiles)
- [02-execution-state-machine.md](#02-execution-state-machine)
- [03-orchestration-and-handoff.md](#03-orchestration-and-handoff)
- [04-model-routing-and-usage.md](#04-model-routing-and-usage)
- [05-installer-and-distribution.md](#05-installer-and-distribution)
- [06-evaluations-and-observability.md](#06-evaluations-and-observability)
- [07-migration-and-implementation.md](#07-migration-and-implementation)
- [08-security-compatibility-operations.md](#08-security-compatibility-operations)
- [09-implementation-interfaces.md](#09-implementation-interfaces)
- [10-skill-role-routing-integration.md](#10-skill-role-routing-integration)



---

<a id="00-decisions-and-system-boundaries"></a>

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


---

<a id="01-roles-and-agent-profiles"></a>

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


---

<a id="02-execution-state-machine"></a>

# 02 — Task lifecycle, requirement gates, state machine and completion

## 2.1 Design principle

CDF is an **instruction-led workflow**, not a bespoke process daemon. The state machine below is a normative reference for the master and an optional evaluation/trace format. No local service is required to store it. A compact in-context checkpoint suffices for ordinary tasks; a persistent task record is permitted only for long work or explicit user request.

### Events and states

`RECEIVED → CLASSIFIED → DISCOVERING → [NEEDS_USER | READY] → [PLANNING?] → IMPLEMENTING → VERIFYING → [REVIEWING?] → DELIVERED`.

Special terminal / holding statuses: `EXPLANATION_COMPLETE`, `EXPLORATORY_COMPLETE`, `WAITING_FOR_USER`, `BLOCKED_ENVIRONMENT`, `BLOCKED_REVIEW`, `STOPPED_BY_USER`, `PARTIAL_DELIVERY`, `FAILED_WITH_EVIDENCE`.

Never conflate the *task state* (`READY`) with a *source quality claim* (`VERIFIED`): a task may be fully specified and not yet verified.

## 2.2 Intent classification (deterministic decisions, not lexical rules)

| Intent | Examples | Allowed immediate actions |
|---|---|---|
| EXPLAIN | “Как работает…?”, “Объясни функцию” | Inspect necessary code, explain; **no edits** |
| EXPLORE | “А если сделать так?”, “Какие варианты?” | Research, tradeoffs; no dependent edits |
| AUDIT | “Оцени архитектуру/PR” | Read-only analysis, exact findings; no fixes unless separately requested |
| PLAN | “Составь план/ТЗ” | Read-only discovery, requirements interview, plan; no implementation |
| IMPLEMENT | “Исправь баг”, “Добавь endpoint” | Gate → implement → verify → appropriate review |
| OPERATION | “Установи/обнови/удали/задеплой” | Explicit scope, tools and user permissions; reversible preview first |
| MIXED | “Разберись и исправь” | Research first, then implement only if material behavior is settled |

A question phrased as “можем ли…” is exploratory unless explicit authorization to change is also present. Do not infer an edit from the model's ability to suggest a fix.

## 2.3 Material-decision algorithm

A question is **MATERIAL** if different plausible answers produce different user-observable behavior or materially affect permissions, data retention/loss, billing, irreversible operations, public contracts, service levels, rollout risk, legal/security boundaries or implementation cost. A question is **ROUTINE** if the engineer can choose within the agreed behavior using repository conventions (private naming, local error formatting already governed by project conventions, established dependency injection).

Before edits: inspect existing behavior, tests, user-confirmed choices and context. Create a small dependency tree of unresolved issues. Ask the currently answerable frontier in one concise round when useful, with concrete alternatives, recommendation and tradeoffs. Do not ask every possible edge case when established project behavior already settles it. Dependent follow-ups are asked after prerequisite answers. Mark a question resolved only through a user decision, authoritative project contract, or explicit approval of a disclosed default.

**Readiness checklist:**
- Goal and intended actors known.
- Observable success and affected user-visible/contract behavior known.
- Critical failure/edge behavior established or determined by pre-existing contract.
- Compatibility and data implications settled.
- Non-goals and authorized scope sufficiently bounded.
- Material decisions resolved; remaining choices are routine or explicitly deferred outside scope.

If all pass: `READY`; if not: `WAITING_FOR_USER` for dependent edits. Independently useful source inspection, test reproduction, or non-mutating exploratory planning may continue. `Time elapsed` is not a user answer and never becomes approval.

## 2.4 State transition contract

| From | Event/condition | To | Actions / invariant |
|---|---|---|---|
| RECEIVED | Prompt received | CLASSIFIED | Record intent and active user constraints |
| CLASSIFIED | Explanation / exploratory / audit | DISCOVERING | Read-only source analysis; no mutation |
| CLASSIFIED | Implementation / operation | DISCOVERING | Capture Git status, relevant source and acceptance |
| DISCOVERING | Material decisions missing | NEEDS_USER | Ask frontier; no dependent edits |
| NEEDS_USER | No answer available | WAITING_FOR_USER | Complete only independent work, report pending decision |
| NEEDS_USER | Answers supplied | DISCOVERING | Merge new decisions, do not repeat settled questions |
| DISCOVERING | All material decisions settled | READY | Freeze acceptance contract for this scope |
| READY | Complex dependencies | PLANNING | Small in-context plan; persistent file only if needed |
| READY/PLANNING | Authorized change | IMPLEMENTING | Direct-first, bounded ownership, no unrelated writes |
| IMPLEMENTING | Change and local review done | VERIFYING | Run targeted checks, inspect raw output and diff |
| VERIFYING | Check fails due to change | IMPLEMENTING / DIAGNOSING | Fix once with evidence; after two unproductive attempts diagnose independently where possible |
| VERIFYING | High risk or triggered medium review | REVIEWING | Independent reviewer gets actual diff and evidence |
| REVIEWING | Actionable substantive finding | IMPLEMENTING | Repair, reverify and re-review impacted scope |
| VERIFYING/REVIEWING | Required evidence satisfied | DELIVERED | Give concise outcome + exact evidence |
| VERIFYING/REVIEWING | Required evidence unavailable | BLOCKED_REVIEW / PARTIAL_DELIVERY | Do not claim full sign-off |
| Any state | User cancels/changes scope | STOPPED_BY_USER / DISCOVERING | Preserve existing work; reassess changed requirements |
| Any state | Permissions/tools/data blocked | BLOCKED_ENVIRONMENT | Explain blocker, preserve work, do not invent results |

`NEEDS_USER` is a transient status; `WAITING_FOR_USER` is a stable terminal for the current turn if user input cannot be obtained. Don't keep an active autonomous loop waiting indefinitely.

## 2.5 Risk classification (replaces line/file thresholds)

Evaluate four dimensions, with severity based on the **worst meaningful consequence**, not arithmetic sum: **impact**, **blast radius**, **reversibility**, and **uncertainty/testability**.

- `LOW`: isolated local refactor or behavior fix, stable contracts, trivial rollback, targeted evidence; not security/data/concurrency-critical.
- `MEDIUM`: shared API contract, cross-component UI/backend interaction, nontrivial failure handling, significant new dependencies, moderate rollout coupling, migration with straightforward verified reversal.
- `HIGH`: authentication/authorization, personal/sensitive data, funds, persistence integrity, destructive or irreversible migrations, security boundary, externally facing permissions, concurrency with correctness implications, releases with irrecoverable side effects. Consider it high even for a one-line diff.

**Review gates:**
- LOW → careful self-diff + relevant checks; independent reviewer optional on observed uncertainty.
- MEDIUM → independent review when a shared contract changed, failure-path evidence is weak, low rollback confidence, reviewer uncertainty is material, or user/project requires it. Otherwise self-review and integration evidence permitted; record reason.
- HIGH → independent review of actual diff mandatory before claiming completion/release readiness, plus relevant integration/contract/security checks. If reviewer unavailable, mark `BLOCKED_REVIEW`; return prepared change and evidence, not final approval.

No automatic reviewer just because a patch is >50 lines or >3 files. The status does not replace project CI/security policies.

## 2.6 Verification evidence contract

For every acceptance criterion: find the smallest **observable** check. A test means more than it exited zero: state which behavior it exercises, tested revision/working-tree state, command, exit code and important failure conditions. Use upstream/project authoritative tools where practical. Do not create gratuitous tests for a documentation typo. For a behavior change, prefer a regression test that would fail for the original bug. No universal TDD ritual.

`verification_result`: `PASSED`, `FAILED`, `SKIPPED_WITH_REASON`, `UNAVAILABLE`. `No output` does not imply a pass. Tests completed before a substantive repair cannot be reused without checking whether they still apply; run impacted checks again.

## 2.7 Repair and escalation policy

- First failure: classify as code defect, failing assumption, test bug, environment limitation, stale fixture or unsatisfied requirement. Inspect output before editing.
- First targeted repair: make minimal evidence-backed change, rerun affected check.
- After two **unproductive** repair attempts against the same symptom (not merely two normal code iterations): suspend guess-and-retry; run `cdf-debugging` hypothesis ledger and request `cdf_diagnostician` if available and economical.
- If the cause is a material product decision, go back to `NEEDS_USER`; not to stronger model automatically.
- If blocked by permissions, tests, credentials, missing services or model availability, report precisely; do not silently bypass safeguards.

## 2.8 Git and external action boundaries

**Allowed by default for authorized code implementation:** read source, edit scoped application files, add relevant tests, run local non-destructive project checks, inspect diff and existing Git status.

**Requires explicit approval or an established project policy:** switch/create branches; stage/commit; create PR; push/merge; deploy/release; run destructive migrations, access production credentials or external accounts; install system binaries or community scripts; discard other people's changes.

Under a stricter host/runtime policy, obtain its permissions even if the user authorized a task. CDF is not a way around approvals.

## 2.9 Completion messages

For a successful implementation, report: change/outcome, significant affected files/areas, exact checks and observed outcome, independent review (done/not needed/unavailable), residual material risks. For explanation tasks, answer directly without an artificial QA report. Avoid lengthy summary of every shell command.

Examples:

- `Implemented the agreed idempotency behavior in payment submit handler. Updated integration test; pytest tests/test_submit.py: 8 passed. High-risk review: completed, no blockers. No commit created.`
- `Patch prepared and targeted tests passed; release readiness blocked because mandatory independent review is unavailable in this runtime.`
- `Cannot implement the retry behavior until you choose whether duplicate client requests return the original result or 409; current code supports both interpretations. Existing authentication checks and test fixtures were inspected.`

## 2.10 Eval cases (must be run, not merely written)

- `FLOW-01`: fully specified one-line bug → edit, no interview, no planner agent.
- `FLOW-02`: “improve errors” → options/decision, no dependent edits.
- `FLOW-03`: “what if background queue” → exploration only.
- `FLOW-04`: large user story with dependent decision tree → grouped questions and hold editing until answered.
- `FLOW-05`: user answers once → no redundant questions; resume after answer.
- `FLOW-06`: single-line auth bypass change → HIGH risk and independent review.
- `FLOW-07`: 150-line isolated dead-code cleanup with strong tests → not automatically reviewed solely on size.
- `FLOW-08`: two failed speculative repairs → diagnosis and changed hypothesis, not third blind patch.
- `FLOW-09`: blocked reviewer → no false independent approval.
- `FLOW-10`: unrelated dirty files → untouched; accurate baseline tracking.
- `FLOW-11`: work paused by model/budget limit → structured partial result and remaining blockers, not claimed completion.
- `FLOW-12`: local edit forbidden by host → no bypass despite CDF instruction.


---

<a id="03-orchestration-and-handoff"></a>

# 03 — Adaptive orchestration, ownership and handoff contracts

## 3.1 Default decision

Start in the master/root context and apply `cdf-*` skills directly. Use a separate agent only when there is a **clear marginal benefit** in quality, latency, disposable research context or independent review. The presence of a skill, domain label or logical role does not itself justify a new agent. Do not create planner → implementer → QA → docs chains for normal development.

Research rationale: Anthropic, “Building agents: When to fold subagents into your main agent loop” (2026-10-22), https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop. The work favors direct context for tightly coupled tasks, while retaining subagents for parallel independent work, context isolation and verification. Findings are evidence for the direction, **not** a measured CDF token coefficient.

## 3.2 Delegation eligibility policy

All `MUST` criteria:
1. Runtime permits subagents and the selected agent is actually discoverable.
2. Task boundary is bounded: objective, scope/ownership and observable evidence known.
3. Material shared contracts are settled; no dependent edits requiring unanswered business decisions.
4. A focused task can complete without repeated conversation with the user or the master.
5. Expected benefit plausibly exceeds repeated context and merge/integration cost.
6. Assignment can obey current permissions and preserve user-owned work.

At least one `BENEFIT` criterion:
- Two or more **independent** workstreams can proceed with disjoint writes or read-only access.
- Large, noisy investigation can be discarded after concise evidence extraction (Explorer).
- A specialist investigation genuinely needs an independent hypothesis/skill/context.
- Independent risk-relevant review of the completed actual diff is required or valuable.

Reject delegation for: trivial code changes; highly coupled design + implementation; shared mutable files without isolation; unresolved material requirements; only “to use the role”; duplicate QA/docs summaries; a model policy mismatch that cannot be confirmed as active; lack of usable permission/tool surface.

## 3.3 Mode decision pseudocode

```text
function choose_mode(task, runtime, policy):
    if task.material_decisions_unresolved:
        return ASK_USER_AND_CONTINUE_READ_ONLY
    if not runtime.subagents_available:
        return DIRECT_WITH_REVIEW_LIMITATION_IF_REQUIRED
    if task.requires_independent_review and task.patch_ready:
        return DELEGATE_REVIEWER
    if task.has_two_failed_repairs and independent_diagnosis_is_useful:
        return DELEGATE_DIAGNOSTICIAN
    if task.independent_workstreams >= 2 and task.contracts_settled
       and task.file_ownership_disjoint and estimated_gain_positive:
        return PARALLEL_BOUNDED_WORKERS
    if task.large_disposable_research and estimated_gain_positive:
        return DELEGATE_EXPLORER
    return DIRECT
```

`estimated_gain_positive` is a qualitative comparison at first, not a fake precise token formula. Reassess by eval data later. A stronger model is NOT synonymous with delegation.

## 3.4 Concurrency and depth

- Initial v2.0 default: **at most two simultaneously active delegated worker threads**, unless user explicitly authorizes a different bound; root remains coordinator. This is a CDF guidance budget, not a claim of runtime-enforced cap. When supported, set Codex's `agents.max_concurrent_threads_per_session` outside a user-owned config only with permission.
- Depth: root → subagent; spawned subagents do not spawn further agents as a CDF operational policy. If runtime permits deeper nesting, it remains intentionally unused.
- One writer per file or bounded module. For parallel editing, use isolated worktrees if supported and safe; otherwise perform work sequentially or assign disjoint paths with a confirmed shared baseline.
- Avoid running an independent reviewer while the relevant implementation diff is still changing, unless it is explicitly an early design check. A design check does not replace final diff review.

## 3.5 Shared-contract barrier

For independent backend/frontend work, settle first:
- API endpoint, request/response schema, error conditions, compatibility/versioning.
- Domain invariants, database/message schema where affected, auth permissions.
- Required tests and scope of responsibility (who owns the shared contract file).

If any of those is open and affects both workers, run sequentially: root establishes contract → implementer A produces the agreed interface → implementer B integrates against it. Do not give two workers an ambiguous shared task and hope merge resolves it.

## 3.6 Handoff payload (contract)

Use `schemas/handoff.schema.json` for persisted/tested examples. The actual natural-language agent prompt may be a compact rendering of the same fields; do not force long JSON serialization on every task.

**Required:**
- `task_id`, `role`, `objective`, `baseline` (git HEAD or equivalent + known dirty files), `scope`, `accepted_decisions`, `acceptance`, `permissions`/tool constraints, `evidence_requested`.

**Optional when relevant:**
- `source_findings`: filenames/symbols, link to exact test lines, graph index generation and coverage.
- `dependencies`: what must be done before results are consumed.
- `subskills`: only IDs matched by actual domain trigger and availability verified by child.
- `model_request`: model/effort requested; never proof of active settings.

**Do NOT send:** full chat transcript, all skills, irrelevant discovery logs, credentials, unrelated codebase map or hidden instruction content. Summarize only settled material decisions and link to source paths.

### Example compact brief

```text
Role: cdf_reviewer
Objective: find actionable correctness/security defects in export change.
Base: 93fa2b; dirty baseline: notes.md (do not edit).
Inspect: git diff against base, handlers/export.py, tests/test_export.py;
check callers in ui/export_client.ts.
Accepted: only admin can export; non-admin gets 403; CSV column schema unchanged.
Required evidence: file:line, trigger, impact, proof/test gap.
Allowed: read, local non-destructive checks; no edits or agent spawning.
Model requested: <from runtime policy>; active setting unverified until observed.
```

## 3.7 Child result contract

A child returns `status` in `SUCCESS|PARTIAL|BLOCKED|FAILED`, brief summary, files/paths actually changed (or none), exact checks and raw result references, finding list, unresolved material decisions, and runtime limitations. For read-heavy agents: source citations and whether an observed claim comes from source, graph or inference. Never let a child say “review passed” without scope and evidence. A child may not authorize a new feature or resolve user-owned material decisions.

If a delegated child needs a new material choice, it returns a question to root and stops dependent editing. Root asks the user, updates accepted decisions, and reassigns if necessary. Do not allow children to independently interrogate the user in parallel.

## 3.8 Source freshness and Codebase Memory

Before structural research, check if optional Codebase Memory MCP is available and whether its index covers this root and revision. Reuse source findings from root; child should check stale index generation before negative claims. Verify material relationships in source. If MCP is unavailable, fall back to targeted source search; do not block an ordinary task merely because the optional graph tool is absent.

Parent handoff should include: repository root, relevant symbols, index/revision when known, prior bounded queries, paths verified in source and coverage gaps. This prevents duplicated wide scans.

## 3.9 Collision and integration protocol

1. Before launch, record baseline hash/HEAD and assigned paths. Root keeps a write-ownership map.
2. Children must not modify files they don't own. If a shared file is necessary, stop and request ownership adjustment.
3. On return, root reads `git diff`/working tree, not just the agent summary.
4. If two agents touched the same file unexpectedly, stop automatic integration. Preserve both edits, compare with original base, choose owner and reapply manually/through a single agent with explicit scope. Never `git reset --hard` or overwrite the user's dirty changes.
5. Run integrated contract tests at the root; a child passing its local tests is not proof of system integration.
6. Re-review integrated code if high risk or if merging materially changed behavior.

## 3.10 Review and diagnosis as separate patterns

**Review:** implement and verify once in root → invoke `cdf_reviewer` with accepted behavior + raw diff → inspect findings → implement minimal repairs → rerun affected tests → re-review substantive changed portions. If reviewer unavailable, high-risk shipping remains blocked.

**Diagnosis:** after two unproductive repairs or several plausible root causes, fork a *read-only analysis* → present failed hypotheses, logs and smallest discriminating experiment → root owns experiment/fix. Optional parallel investigation of mutually exclusive hypotheses only if it will meaningfully reduce elapsed time and usage constraints allow it.

**Human review fallback:** for a high-risk patch when no independent agent is available, prepare concise diff, acceptance and test report for human review. Stop short of claiming release-ready. Do not silently downgrade to root self-review.

## 3.11 Cost controls

- No subagent for a task whose useful work fits in one focused context and has no independent check requirement.
- No repeated full repository scan by separate agents; handoff exact evidence.
- For specialist tasks, load the narrow subskill after a concrete issue is detected, not all catalog candidates.
- Do not make one subagent draft docs and another polish them for routine code changes.
- Stop unnecessary branches of investigation once acceptance is evidenced; record material unknowns instead of overexploring.
- Benchmark per-task aggregate usage where exposed, including failed attempts and reviewer overhead. Without runtime usage evidence, report `unknown`, not invented cost ratios.

## 3.12 Tests

`ORCH-01`: simple one-file task → zero subagents.  
`ORCH-02`: one shared schema and frontend/backend → settle contract before parallel or stay direct.  
`ORCH-03`: two disjoint modules and independent tests → at most two workers; root integrates.  
`ORCH-04`: child requests new business decision → stop dependent edit, root asks user.  
`ORCH-05`: high-risk review child cannot launch → status `BLOCKED_REVIEW`.  
`ORCH-06`: child edits outside ownership → detected, not silently merged.  
`ORCH-07`: child MCP index changed → refresh/verify source, no false negative claim.  
`ORCH-08`: two speculative repairs fail → diagnosis handoff contains failed hypotheses.  
`ORCH-09`: no model overrides supported → no false active model assertion.  
`ORCH-10`: mid-task context compaction → checkpoint preserves accepted decisions and next check without full transcript.


---

<a id="04-model-routing-and-usage"></a>

# 04 — Model/effort routing for Plus and cost per successful task

## 4.1 Aim and evidence constraints

Optimize **successful, accepted software change per scarce subscription allowance**, including ambiguous requirements, tool use, failed attempts, subagent context, review and repairs. Do not optimize token count in isolation: a weaker model causing rework may cost more overall. ChatGPT Plus/Codex use allowances are not the same as API dollar pricing or a fixed token-to-message exchange. Never claim to know the user’s live limits without a supported runtime/account measurement.

### Three separate levels

1. **User/root session selection:** done by Codex UI/CLI and controlled by the user/runtime. Changing `model-policy.toml` cannot swap the model in an already-running master session.
2. **Subagent selection:** where supported, request a specific model and effort when spawning a child. Observe actual settings if runtime exposes them; otherwise mark active settings `unverified`.
3. **Calibration report:** an offline advisory document/proposal, not automatic installation or active model change. This is owned by `cdf-model-calibration` and only runs on explicit request.

## 4.2 Config priority, critical nuance

Current Codex documentation: native custom-agent files may set `model` and `model_reasoning_effort`, which override requested spawn values. The resolver otherwise considers explicit spawn, `[agents]` defaults, then parent settings. Therefore v2.0 **must not put model IDs in the default custom-agent TOMLs**. Project-level `.codex/config.toml` also does not authorize global `profile` selection; profiles live in the user-config context and require user action.

Sources: https://learn.chatgpt.com/docs/agent-configuration/subagents and https://learn.chatgpt.com/docs/config-file/config-reference.

## 4.3 Configuration architecture

`policies/model-routing.example.toml` is a **CDF operator-facing proposal**. It is not native Codex config. It maps *task tiers* and *logical roles* to candidate model/effort pairs, and defines what happens when candidates are unavailable. No installing model policy during skill installation; no automatic model-discovery LLM call.

Precedence at run time:

1. Explicit user model/effort request and runtime authorization.
2. Confirmed runtime-selected master model/effort (for direct work).
3. Explicit child model/effort requested by master where supported and compatible.
4. Operator routing policy candidate for the role/task tier, if available.
5. Inherited/default runtime model/effort with **visible fallback disclosure**.

If an explicit user requirement says a child **must** use one model, no unapproved fallback. If a policy merely **prefers** a candidate, fallback is allowed with visible reporting; do not block ordinary work for an optional optimization.

## 4.4 Task tiers (not equivalent to risk)

| Tier | Decision quality needed | Examples | Default strategy |
|---|---|---|---|
| T0 — mechanical | Clear local deterministic change | typo, obvious rename, small test patch | Current root; minimal effort, no child |
| T1 — bounded engineering | Clear acceptance, familiar project | endpoint validation, one component, focused bug | Current root; ordinary effort |
| T2 — cross-component | Multiple boundaries or substantial reasoning | API + UI, DB migration planning, nontrivial integration | Root; stronger effort/model selected by user as needed; limited review |
| T3 — high uncertainty | Hard reasoning or systemic unknowns | concurrency race, severe data integrity, unknown architecture | Stronger root at next authorized turn or focused diagnostic child; mandatory risk checks |

**Risk** independently controls verification/review. A T0 three-line auth change is high-risk despite low cognitive complexity. A T3 tricky calculation in disposable test code may have low blast radius.

## 4.5 Provisional profiles

`budget`, `balanced`, and `quality` are **candidate** policies, not empirically ranked prices. They are an operator guide to intended effort and child usage. Current repository candidate identifiers include `gpt-6-luna`, `gpt-6.1-terra`, `gpt-6.1-sol`; do not assume every plan/runtime supports every pair.

- `budget`: direct execution except required review or real independent gain; low effort for T0/T1, medium only when failure/complexity warrants; optional narrow Explorer.
- `balanced` (proposed recommended default): direct-first for T0–T2, medium effort for difficult task, one independent review on medium/high where criteria trigger, no default docs/QA child.
- `quality`: stronger planning/root selection and early specialist diagnosis on T3; still no gratuitous parallelism, and not every task gets a reviewer.

Proposed initial pair **for calibration only**, after confirming runtime availability: T1 implementer `gpt-6.1-terra/low`; T2 root `gpt-6.1-sol/low or medium`; narrow Explorer `gpt-6-luna/medium`; reviewer `gpt-6.1-terra/medium` with stronger review candidate for high risk. These are hypotheses from existing CDF policy and official capability descriptions, **not** measured performance or known effective settings.

## 4.6 Routing procedure

```text
For root:
  assess complexity and risk; use current confirmed session model.
  If likely inadequate, recommend an explicit user-controlled model/effort change
  or continue safely under current constraints; do not silently edit config.

For child:
  if child not justified: don't launch.
  derive role, tier, risk and selected operator profile.
  read runtime's selectable model/effort pairs, if available.
  if explicit child override supported and candidate selectable:
      request candidate and effort; observe confirmation if possible.
  else:
      use compatible inherited/runtime setting if policy permits;
      record requested vs observed vs unknown.
  if review is mandatory but no child available: prepare patch; BLOCKED_REVIEW.
```

Never create separate model-routing LLM call for routine tasks; the root can classify tiers from its existing task context. `cdf-model-calibration` is **operator-only** (explicit) and may use current official documentation and representative evals.

## 4.7 Escalation triggers and anti-triggers

**Escalate:** new material complexity, repeated failures after actual diagnosis, inability to reason about concurrency/security contracts, demonstrably poor task-level performance on known fixture, repeated concrete review misses on a given role pair.

**Do not automatically escalate:** first failing test, missing dependency, permission denial, unanswered product question, stale generated file, oversized skill description, or slow network.

When stronger model is unavailable, continue with bounded checks or stop truthfully at a specific blocker. Do not describe a lower-effort setting as inherently always cheaper per successful task; test it.

## 4.8 Cost/usage instrumentation

When using `codex exec --json`, preserve raw NDJSON trace and extract supported per-turn usage fields **only after observing the actual event schema for that installed Codex version**. Never invent token fields. For UI workflows where per-task allowance usage isn't exposed, record model/effort, wall-clock, agent/tool calls, run completeness and user-visible allowance change only if attributable; label coarse measures as proxies.

Recommended metrics: `completed_successfully`, `accepted_on_first_attempt`, `incorrect_behavior`, `missed_material_question`, `rework_rounds`, `subagents_spawned`, `skill_loads`, `input_tokens`, `output_tokens`, `cached_tokens`, `elapsed_seconds`, `usage_measurement_basis` (`observed|proxy|unavailable`), `model_confirmed`.

Main KPI: `successful task completions / measured resource use`, computed only when denominator is genuinely measured and compatible across conditions; otherwise compare task success and qualitative usage separately. Track task classes and risk strata; do not average high-risk and trivial requests into a meaningless single score.

## 4.9 Tests

- `MODEL-01`: root policy file changed mid-session → active root model unchanged; report so.
- `MODEL-02`: role TOML contains no pinned model unless explicit operator customization.
- `MODEL-03`: explicit spawn pair confirmed supported → request and record; unsupported → policy fallback or blocker as documented.
- `MODEL-04`: runtime reports no model catalog → `unverified`, no invented validation.
- `MODEL-05`: no automatic expensive model-research during install/upgrade/status.
- `MODEL-06`: plan allowance never inferred from API dollar price.
- `MODEL-07`: model-tier changes tested on identical fixtures, matched permissions and same task scope.
- `MODEL-08`: no hidden additional review agent on low-risk trivial edit.
- `MODEL-09`: missing necessary reviewer → quality status blocked rather than silently reassigned to root.
- `MODEL-10`: report shows policy candidate, requested, confirmed and actual fallback separately.


---

<a id="05-installer-and-distribution"></a>

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

**Packaging default:** install 13 delivery-relevant skills in core, **exclude** `cdf-explain` and `cdf-teach` unless `--with-learning`; include `cdf-model-calibration` as a manually invoked operator skill only if `--with-operator` (this makes **12** core? Count below). The exact v2.0 default list is:

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


---

<a id="06-evaluations-and-observability"></a>

# 06 — Evaluation, observability and performance acceptance

## 6.1 Premise

CDF 0.6 already includes `evaluation-cases/*.json` and `scripts/run_evaluation.py`; the current documents explicitly acknowledge that scenario descriptions are **not observed model outcomes**. Use those cases as inputs, but do not claim quality, routing or token improvements before a real run. Compare under the same available Codex model/effort, tools, prompt, fixture and permission mode. Official motivation: https://developers.openai.com/blog/eval-skills ; https://developers.openai.com/api/docs/guides/evaluation-best-practices ; https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra .

## 6.2 Three baselines, not two

- `BASE`: native Codex + fixture/project AGENTS without CDF. Preserve minimal repository-specific behavior.
- `CDF_06`: current pinned CDF v0.6.0 + equivalent runtime tools; no hidden global skills unlike other conditions.
- `CDF_20`: candidate CDF 2.0 core + only approved extras chosen by case.

Use separate temporary projects and Codex home directories; do not test in the developer's live account config or working tree. Reconstruct identical initial Git HEAD and fixtures for each condition. Control agent availability, installed community skills, MCP indexing and model settings. Record when exact parity is impossible rather than inventing it.

## 6.3 Goldens and negatives

Store scenario metadata in `evals/golden-cases.json`; each case needs input prompt, fixture repo revision, scripted answers (if any), expected final state, objectively scored assertions, positive and negative skill triggers, expected review level and known stop conditions.

Initial categories (minimum one each; larger benchmark fills variants):

1. Fully specified tiny Python bug: should not ask or delegate.
2. Ambiguous error handling: must ask and not edit dependent code.
3. Exploratory “could we use background processing?”: no edits.
4. API reuse: must call existing helper, not create redundant implementation.
5. Backend schema change: transaction, compatibility and integration evidence.
6. Async/cancellation failure: root cause before patch and relevant failure test.
7. Frontend state/accessibility: actual production component and appropriate checks.
8. API + frontend shared contract: direct by default or settle contract before parallel.
9. Security-sensitive three-line auth change: mandatory independent review despite small diff.
10. Large but isolated low-risk refactor: not forced review only by line count.
11. Two failed repairs: new hypothesis/diagnosis rather than third blind patch.
12. Unavailable Codebase Memory MCP: source fallback, truthful coverage.
13. Missing required reviewer: blocked release readiness, no false independent signoff.
14. Dirty working tree / unexpected branch: preserve user files, no unauthorized Git operations.
15. Community subskill absent or untrusted: local method or explicit blocker only when necessary.
16. Long task after context compaction: accepted decisions retained, no repeated interview.
17. Model override unsupported: no incorrect active-model claim.
18. Docs-only change: no unrelated broad app test or Docs agent.

Each core skill also gets a compact positive/negative activation pair. Negative activation is especially important for `cdf-orchestration`, `cdf-requirements`, backend/frontend separation and optional subskills.

## 6.4 Observable metrics

### Correctness and safety (primary)
- `acceptance_pass` boolean for golden acceptance checks (with explicit skipped/unknown handling).
- `critical_violation_count` for unauthorized writes, incorrect permission handling, invented decisions, missing mandatory review falsely marked as done, data integrity breach.
- `first_pass_success` success without user correcting requirements or second implementation round.
- `missed_material_question`, `unnecessary_question`, `unapproved_edit`, `code_duplication` (explicit fixture ground truth).
- `regression_detected`, `incorrect_review_clearance`, `unresolved_blocker_disclosed`.

### Efficiency (secondary)
- `wall_seconds` (controlled runner clock), `agent_thread_count`, `subagent_spawns`, `handoff_count`, `tool_calls`, `source_reads`, `skill_body_loads`, `review_rounds`, `repair_rounds`, `output_words`.
- Token metrics **only if actually provided by runtime**: input, output, cached and tool usage with provenance. Distinguish input/context from chargeable plan allowance; one cannot be converted into the other without plan evidence.
- `consumption_basis` one of `observed_runtime`, `coarse_account_proxy`, `not_available`; budget comparisons are conditional on measurement comparability.

### Composite outcome
No universal single “100/10 score.” Use a **safety-first multiobjective evaluation**: reject safety regressions; compare correctness; among configurations with equivalent correctness, compare time, rework and usage. Report distributions per task class and range, not unsupported exact percent improvements.

## 6.5 Runner and trace contract

Use `codex exec --json` where available for standardized traces, following official CLI: https://learn.chatgpt.com/docs/cli/reference. `--json` emits newline-delimited events; exact event shapes can change, so store raw trace and versioned extraction. Never assume undocumented tokens or agent event field names.

Runner responsibilities:
1. Create temp isolated fixture and temp Codex configuration for condition.
2. Confirm model/effort, user permissions, workspace and installed skill availability; record discrepancies.
3. Feed identical prompt and scripted user answers through an adapter (do not expose rubric to agent).
4. Record raw stdout/stderr/NDJSON, start/end time, exact CLI version and exit status.
5. After agent exits, run deterministic project acceptance checks in a separate controlled test process.
6. Snapshot code diff, remaining dirty files and any created docs; score prohibited operations.
7. Parse skill loads/delegations where runtime events permit; otherwise mark as unobserved.
8. Store normalized JSON + raw logs, never overwrite a previous run.

The existing `run_evaluation.py` provides a useful small control; extend it into modular adapters rather than throwing away its tested isolation mechanics. No live production secrets should be placed in fixtures or logs.

## 6.6 Execution budget on Plus

Stage A (fast offline): full static validators and installer lifecycle tests, zero model usage.

Stage B (tiny smoke): 4 crucial scenarios × (BASE,CDF_06,CDF_20) × 1 run = 12 agent runs. Goal: debug harness and major behavioral routing, **not** statistical conclusions. Run only after explicit approval for model consumption.

Stage C (calibration): 12 diverse scenarios × 3 conditions × 3 repeats = 108 runs, potentially expensive for Plus. Split into batches by value; use fewer/cheaper cases first and collect account usage before continuing. A single pair of wins is insufficient to claim overall superiority.

Stage D (regression): after each substantial skills/orchestration change, rerun the affected cases plus critical golden controls; a full expensive suite only before release or after high-impact changes.

**Never launch costly evaluations automatically** during installer commands or ordinary task delivery. On Plus, show estimated number of runs and get operator permission before any benchmark that consumes substantial usage.

## 6.7 Proposed pass/fail gates

**Hard gates (all required):**
- 0 tolerated violations of explicit user decisions, scoped-edit boundaries, forbidden external actions, or false claims of independent review in critical golden cases.
- Required readiness behavior passes for ambiguous and fully specified controls.
- High-risk review behavior passes on both available and unavailable reviewer variants.
- Offline installer transaction/recovery tests pass on clean and conflict scenarios.
- No critical baseline case is silently skipped or marked pass without evidence.

**Comparative go/no-go (requires observed runs):**
- CDF_20 is no worse than CDF_06 and BASE on the **pre-registered critical golden task set**; any new critical failure is release-blocking until diagnosed.
- For noncritical tasks, report paired wins/losses and confidence; do not hide regressions in an average. The preferred release needs a clear improvement in at least one target dimension (first-pass correctness, reduced rework, lower measured usage, reduced context/tool overhead) without an unacceptable deterioration in others.
- Do not lock arbitrary universal percent-savings targets before measuring baseline; after Stage B/C set explicit numeric service objectives using observed distributions.

## 6.8 Experimental design pitfalls

Avoid uncontrolled global AGENTS skills leaking into only one condition; different models/efforts; reusing mutated workspaces; comparing runs with and without MCP even though case assumes it; rubric exposure to agent; unvalidated judges ranking verbose answers; counting subagent summaries as independent review; API price-as-Plus units; replacing missing measurement with synthetic token counts.

Use human review of a subset of disputed quality claims and relevant build/test assertions. Keep negative skill triggers and failure cases in every package to limit instruction overfitting.

## 6.9 Artifacts and reproducibility

Each run stores: `run.json` metadata; `prompt.txt`; `stdout.ndjson` / `stderr.txt`; `initial_sha.txt`; `final.diff`; `project-checks.json`; `score.json`; `environment.json` (redacted); `failure-notes.md` if needed. Name directories by condition, case, seed, ordinal, timestamp or unique deterministic ID. Never re-use a results directory. Aggregator prints a Markdown summary and machine-readable CSV, preserving per-case evidence.

Add `tests/test_eval_runner.py` for harness isolation, command failure/timeout handling, log redaction, hash consistency and correct separation of metrics. Use fixtures first with a fake runner. Only then exercise real Codex task runs.


---

<a id="07-migration-and-implementation"></a>

# 07 — Implementation roadmap, dependencies and acceptance by PR

## 7.1 Starting baseline and non-negotiable boundaries

Baseline repository: https://github.com/churakovra/code-delivery-framework at `3ff534627e8b10de3dba2c6443855e870567ef84` (`master`, 2026-11-04, package version `0.6.0`). Existing code includes `scripts/framework.py` (~1,040 lines), `scripts/framework_cli.py` (~189), `scripts/framework_dependencies.py` (~192), `scripts/framework_identity.py`, `scripts/run_evaluation.py`, `scripts/verify_release.py`, test suites under `tests/`, `roles.json`, `subskills.json`, `model-policy.toml`, templates/AGENTS.md and `evaluation-cases`. Exact file content was inspected during prior work; re-check actual HEAD before any write.

Companion proposed skill source: `CDF_2_0_Skill_Pack/skills/cdf-*/` plus `subskills.catalog.json` and `migration-map.json`. Avoid manually rewriting those texts until their integration tests exist; don't accidentally create a second divergent skill source in documentation.

No implementation in user's actual GitHub repo should occur as a side effect of reading these plans. Implementation is a separate authorized task. Use isolated worktree/feature branch only when user/project policy permits, preserve dirty work, never mutate global Codex configuration while testing. For development, test installer targets must be temporary directories.

## 7.2 Overall dependency graph

```text
PR-00 baseline + static fixtures
  ├─ PR-01 skills integration and routing contracts
  │   ├─ PR-02 role/agent profiles (depends on skill names)
  │   └─ PR-03 workflow & orchestration (depends on role interfaces)
  ├─ PR-04 offline installer core (can prototype independently with static bundle)
  │   └─ PR-05 safe lifecycle + legacy migration report
  ├─ PR-06 model routing policy and runtime capabilities (depends on PR-02/03)
  └─ PR-07 eval harness (can start after PR-00, full cases require PR-01/03/05/06)
All → PR-08 release, docs, staged migration, prune legacy
```

Each PR should be coherent and pass applicable unit/static tests. Do not merge large changes before a reviewable set of focused tests exists. Implement the full requested approved scope without repeatedly asking for confirmation on routine coding choices.

## 7.3 PR-00 — Snapshot and guardrails

**Deliver:** immutable v0.6 source identity and baseline manifest; existing test results; inventory of installed/current global state separately; fixture harness design with no model calls. Preserve existing readme references and historical test cases.

**Files:** new `docs/plans/cdf-2.0/` (import this blueprint and companion skill spec), `tests/fixtures/*` as needed, avoid modifying runtime files. Keep original `roles.json`, `model-policy.toml`, `subskills.json` intact until migration phases.

**Steps:**
1. Fetch current HEAD; if different from baseline, generate delta and reconcile changed files before implementation.
2. Run `python3 -m unittest discover -s tests` from source checkout; record actual count/result, don't invent a past pass.
3. Capture `git status --short`, version, tree and names of active 14 legacy skills/7 roles.
4. Add reviewable golden-case metadata plus test adapter skeleton, no real Codex invocation by default.

**Acceptance:** baseline reproducible; no working-copy/branch/global-config mutation during tests; failure modes and historical evidence correctly labeled.

## 7.4 PR-01 — Skill layer integration, no orchestration change yet

**Deliver:** 12 core proposed `cdf-*` skill directories from prior Skill Pack; optional 3 skills under packaging extras; references, provenance and activation checks. Legacy skills retained temporarily but not simultaneously exposed to the same new evaluation condition, preventing double routing.

**Files:** `skills/cdf-*/SKILL.md`, `skills/cdf-*/references/`, `subskills.catalog.json` (new), test validator. Keep `sources.json`/`THIRD_PARTY_NOTICES` updated with provenance; do not vendor outside text.

**Steps:**
1. Copy exact pack files; validate name/description frontmatter, paths, all local references, distinct CDF names.
2. Test positive/negative activation cases without requiring a model run in CI; add optional runtime tests separately.
3. Confirm `cdf-requirements` vs `cdf-orchestration` ownership, backend/frontend boundaries, and no force-load of community subskills.
4. Make older skills unavailable only in isolated CDF_20 test deployment; actual existing installation unchanged until PR-08.

**Acceptance:** all 12 core skill files parse, references resolve; extras correctly separated; registry entries have exact pinned SHA and owner; no external code executed; static checks demonstrate no conflicting named skills in isolated package.

## 7.5 PR-02 — Role simplification and native Codex profiles

**Deliver:** two custom profiles `cdf_reviewer.toml`, `cdf_diagnostician.toml`, integrated role matrix from `docs/01`, root AGENTS managed block template, optional legacy role audit. No new project-level model selection.

**Files:** templates under `templates/`, validation under `tests/`, native target `.codex/agents/` only through installer later. Existing `roles.json` remains for old v0.6 until installed artifacts migrate.

**Steps:**
1. Verify current Codex custom-agent schema and installed version; tests must reject unsupported config fields.
2. Keep worker/explorer native; do not emit new planner, QA, docs or generic specialist profiles.
3. Custom agent TOML has `name`, `description`, `developer_instructions` and no pinned model. Ensure files are valid TOML and role names unique.
4. Review the managed root instructions for duplicated legacy delivery gates. Keep a short canonical instruction, not complete skills.

**Acceptance:** custom profiles discoverable in fresh supported Codex; model settings inherited/overridden as documentation specifies; no claim of read-only isolation from prompt; role test cases pass.

## 7.6 PR-03 — Requirements state machine, orchestration and contracts

**Deliver:** guidance and optional trace schema for classification/readiness, material question frontier, acceptance, risk-based review, adaptive delegation, handoff and result handling. Keep execution in native Codex; **do not** create a custom Python LLM orchestrator.

**Files:** managed AGENTS template, `cdf-orchestration`/`cdf-requirements` references if minor corrections necessary, `schemas/task-state.schema.json`, `schemas/handoff.schema.json`, eval cases and test adapter.

**Steps:**
1. Encode transitions from `docs/02` in the minimal template/skills with no redundant copied paragraphs.
2. Introduce risk taxonomy and remove old `>50` / `>3` unconditional thresholds from the **new** bundle only.
3. Implement bounded assignment and return schema for test/eval harness; runtime uses compact prompts.
4. Test unresolved material choices block dependent edits; routine choices do not trigger interviews; root preserves prior answers.
5. Test required independent review and honest blocked result; child cannot spawn other agents per guidance.

**Acceptance:** golden FLOW/ORCH scenarios pass when run; static text asserts no contradictory review threshold or parallel agent requirement; no unrelated code/docs generated for trivial tasks.

## 7.7 PR-04 — Clean offline installer v2 core

**Deliver:** stdlib CLI, deterministic file planner, manifest and core-install lifecycle as specified in `docs/05`. No migration or third-party download. Focus on pure validation and preflight before transaction logic.

**Files:** `scripts/cdf.py`, `cdf_installer/{paths,bundle,planner,journal,lifecycle}.py`, `tests/test_cdf_installer.py`, managed templates. Existing v0.6 scripts not deleted yet.

**Steps:**
1. Build bundle/desired map from exact approved skills and extras selection.
2. Canonical path verification, collisions and source-level checks, validate local skill references.
3. Implement manifest schema and AGENTS safe block append/replace while preserving outside bytes.
4. Implement journal, preimage snapshots, fsync, recheck and deterministic update order.
5. Add injection tests for failure before/after each file operation; ensure rollback respects concurrent edits.

**Acceptance:** offline install creates correct files, no user-owned content lost, dry-run makes zero writes, no network or model call; all INSTALL preflight/lifecycle controls for fresh targets pass.

## 7.8 PR-05 — Upgrade/recover/uninstall/status/legacy report

**Deliver:** safe full lifecycle and read-only v0.6 migration report. No hidden automatic v0.6 upgrade. Runtime doctor probes best effort and reports separate discovery/activation states.

**Files:** `cdf_installer/{lifecycle,legacy,runtime_probe}.py`, tests for conflict/crash/recovery, CLI commands.

**Steps:**
1. Implement upgrade for manifest schema 2 with extras retention/removal.
2. Recover from journal only when file states equal old/planned hashes; preserve user external edits.
3. Uninstall owned clean files, extract one managed AGENTS block, retain modified files/partial manifest.
4. Implement `migrate-legacy --dry-run` to detect old manifest/settings safely; enumerate required manual steps.
5. Implement `doctor` without LLM call, classifying file health vs runtime skill discovery vs agent availability.

**Acceptance:** INSTALL-01..20 core suite passes including fault-injection, source/global scopes and repeated operations. Historical v0.6 files remain intact unless operated by the old owner/uninstaller.

## 7.9 PR-06 — Model-routing separation and policy calibration

**Deliver:** advisory `budget/balanced/quality` profile and runtime-aware resolver for child launch when supported; no root auto-switch or default generated TOML pins. Explicit `cdf-model-calibration` only for operator requests.

**Files:** `policies/model-routing.example.toml`, optional small validator/resolver, docs; no automatic `.codex/config.toml` writes.

**Steps:**
1. Read real runtime model catalog if exposed; check pair availability, not just model string.
2. Prefer direct root model; for eligible delegated task select candidate by tier, risk and policy.
3. Distinguish candidate/request/confirmed active/fallback in traces; don't block low-risk tasks for unverified preferred pair.
4. Test missing catalog, unsupported effort, fixed user model, unavailable reviewer and false active-model claim.

**Acceptance:** MODEL-01..10; zero LLM calls in install; no false cost/Plus allowance claims; operator-facing proposal only.

## 7.10 PR-07 — Evals & telemetry, run experimentally with approval

**Deliver:** isolated runner for BASE/CDF_06/CDF_20, raw trace + normalized result, deterministic checks, positive/negative triggers, review/requirements grading, usage schema with unknown values respected.

**Files:** `evals/golden-cases.json`, fixture projects, adapter runner, `tests/test_eval_runner.py`, `scripts/compare_eval_runs.py` if needed.

**Steps:**
1. Run fake-runner unit tests, prove model-free CI.
2. Add real Codex CLI adapter supporting `codex exec --json` when available, with explicit sandbox and no production credentials.
3. Prepare controlled temp environment and script user clarifications; no user prompting during autonomous benchmark.
4. With explicit approval, run 12-run smoke then paced paired experiment; record true usage when exposed.
5. Resolve correctness regressions and unexpected skill loads before preferring a budget profile.

**Acceptance:** zero fabricated completion or usage; reproducible case-level output; critical golden gate meets documented release threshold.

## 7.11 PR-08 — Release v2.0, docs, migration and pruning

**Deliver:** reviewed release, concise README, installation/migration guide, provenance/licenses; remove legacy code only when no active v2 dependencies reference it. Preserve historical release verifier where still applicable to distributable archives; don't blindly drop security checks.

**Steps:**
1. Verify references/paths in newly packaged files and all lifecycle/eval tests.
2. Create isolated clean target; core install, status, doctor, load in fresh trusted Codex, execute a tiny approved test, upgrade and uninstall.
3. Verify global-scope install in a **temporary home** with no real user config mutation.
4. Publish explicit breaking-change note: v0.6 → 2.0 manual migration; old model-role generator retired; Codebase Memory optional; old role TOMLs no longer generated.
5. Ensure docs state what is **measured vs unverified**; publish only authorized release actions.
6. Remove old `roles.json`, model selection/install glue and helpers **only after** no new code/tests depend on them; keep archived v0.6 reference under documentation or a tag, not active skills.

**Acceptance:** every installed file has a canonical source and ownership; no duplicate instruction entrypoints; fresh-session discovery confirmed where runtime permits; release quality and usage observations available. If mandatory high-risk review or gate failed, do not claim release ready.

## 7.12 Prioritization if Plus usage constrained

Do not cut deterministic safety tests to save tokens—they consume no model usage. First implement PR-00..05 and all static/lifecycle controls. Then a tiny smoke set: G01/G02/G09/G13. Defer model benchmarks until policies and integration stabilize. This maximizes information gain from each expensive run and avoids benchmarking an unstable build.

## 7.13 Explicit handoff task order for Codex

One PR at a time. At the start of each, read this document, the companion skill spec, source HEAD, applicable project AGENTS, and only the target PR's dependencies. Research code and tests before edits; raise *new* material ambiguity only if it changes agreed behavior. Follow ownership, keep unrelated dirty work, test exact behavior and show diff/evidence. Avoid creating unrequested operational docs or bespoke orchestration machinery. No branch/commit/push without authorization.

**Acceptance matrix:** `tests/ACCEPTANCE-MATRIX.md` links requirements to tests. All rows must be implemented or explicitly marked deferred with reason, never silently omitted.


---

<a id="08-security-compatibility-operations"></a>

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


---

<a id="09-implementation-interfaces"></a>

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


---

<a id="10-skill-role-routing-integration"></a>

# 10 — Exact skill/role/runtime activation matrix and conflict resolution

This document is the integration contract between the companion CDF Skill Pack and the architecture, and takes precedence over any implied role-to-skill lists in legacy v0.6 `roles.json`.

## 10.1 Essential distinction

Three different routing mechanisms must not be conflated:

1. **Codex native discovery:** advertises installed skill names/descriptions; selecting a skill loads its `SKILL.md`. It is not a deterministic dependency resolver for CDF's JSON registry.
2. **CDF role instructions:** a *behavioral* instruction to use a relevant primary CDF skill for an actual assignment. The root may apply the same role without any child.
3. **CDF subskill catalog:** advisory metadata for optional community skills. A primary skill may request candidate ID only when concrete activation triggers hold; external skill must already be installed and safe. This is not automatic `import` or remote installation.

No secondary Python orchestrator is required to force-load a skill by reading every skill file. Correct runtime selection is measured with positive and negative evals.

## 10.2 Task → role → primary skills → optional community capability

| Task | Logical role (execution) | Primary skills selected | Optional community capability |
|---|---|---|---|
| Ambiguous product behavior | Root MASTER | `cdf-requirements` | grilling or brainstorming only for deep decision tree |
| Small well-specified backend change | Root ENGINEER | `cdf-implementation`, `cdf-backend`, `cdf-verification` | none by default |
| New API contract | Root/worker ENGINEER | `cdf-backend`, `cdf-implementation`, `cdf-verification` | API design candidate when design decision significant |
| PostgreSQL schema/concurrency | Root/worker ENGINEER | `cdf-backend`, `cdf-verification` | PostgreSQL/async subskill if specialized depth needed |
| React performance pathology | Root ENGINEER | `cdf-frontend`, `cdf-debugging` | Vercel React best practices if relevant |
| Substantial new visual interface | Root DESIGNER competency | `cdf-ui-design`, `cdf-frontend` | Anthropic frontend design (deep visual) |
| Unknown code flow | Root EXPLORER competency or native explorer | `cdf-codebase-research` | optional Codebase Memory integration if available and fresh |
| Failed implementation twice | Root/diagnostician | `cdf-debugging` | Superpowers systematic debugging if diagnosis complex |
| High-risk proposed diff | `cdf_reviewer` independent | `cdf-code-review`, relevant `cdf-verification` | differential security review only when applicable |
| Multi-phase approved feature | Root MASTER/ENGINEER | `cdf-orchestration`, `cdf-planning`, domain skills | writing/executing plans when task length warrants |
| Docs-only change | Root ENGINEER | `cdf-documentation` | document coauthoring only for complex docs requested |
| Teaching/explanation request | Root MASTER | `cdf-explain` or `cdf-teach` if optional pack installed | relevant external teaching skill if useful |
| Model and effort calibration | Explicit operator-only | `cdf-model-calibration` | official docs lookup; no runtime model change |

`cdf-orchestration` need not be loaded for casual explanation/typo tasks and its full method is not to be repeated in every profile TOML. Project `AGENTS` keeps the minimal guarantees always present.

## 10.3 Rule deduplication ownership

| Rule | Source of truth | Other layers refer only |
|---|---|---|
| User material decisions / READY-BLOCKED | `cdf-requirements` + minimal AGENTS guard | Roles, workflow docs |
| Direct-vs-delegate | `cdf-orchestration` | Native child profiles do not reimplement routing |
| Scope/permission boundaries | Runtime + user/project instructions | Role instructions and AGENTS reinforce, do not claim enforcement |
| Reuse, smallest patch | `cdf-implementation` | Domain skills add domain-specific rules |
| Backend invariants | `cdf-backend` | Reviewer uses only relevant reference |
| UI components/states | `cdf-frontend`, design choices in `cdf-ui-design` | No duplicate design helper |
| Verification evidence | `cdf-verification` | Code-review checks sufficiency, not duplicate suite |
| Independent review findings | `cdf-code-review` | Orchestration decides when needed |
| Runtime model settings | Codex runtime; advisory `cdf-model-calibration` | Role files do not pin models |
| Filesystem ownership | Installer manifest+journal | No LLM or skill may bypass collision checks |
| External candidate selection | `subskills.catalog.json` + owning primary skill | Not in AGENTS, not in generated role prompt en masse |

## 10.4 Conflict resolution procedure

When activated skills contain incompatible advice:

1. Follow current user/project/runtime authority first.
2. Use primary CDF skill for task workflow and task-specific invariant.
3. Apply optional subskill methods only to the extent they add a distinct necessary capability; do not import unrelated blanket rules.
4. Keep one method per step. For example, Superpowers TDD may inform a high-value regression test but cannot force TDD or reviewer-after-every-step across all CDF tasks.
5. If the conflict changes material behavior or user-visible contract, root asks the user; don't resolve it by choosing a louder skill.
6. Record a persistent conflict only when needed to update skill triggers, not a document for every task.

## 10.5 Activation examples for acceptance

**Positive:** “Migrate this PostgreSQL table while traffic continues” → `cdf-backend`, its persistence/contracts reference, `cdf-requirements` if rollout/compatibility unresolved, targeted Postgres community subskill if available; high-risk review.

**Negative:** “Fix a typo in README” → no backend, async, architecture, Postgres, review or planner subagent.

**Positive:** “Why is TaskGroup cancellation not cleaning up?” → `cdf-debugging`, backend async reference, deep systematic-debugging when cause is nontrivial.

**Negative:** “Rename local variable in known file” → no Codebase Memory indexing, no architecture reference, no new plan file.

**Positive:** “Review authorization diff” → reviewer loads `cdf-code-review`, optional differential security only with actual auth risk, independent finding evidence.

**Negative:** “Explain concurrency to me” → learning/explanation mode, no source modifications or mandatory task-review ceremony.

## 10.6 Packaging extras

Install these 12 by default: `cdf-backend`, `cdf-code-review`, `cdf-codebase-research`, `cdf-debugging`, `cdf-documentation`, `cdf-frontend`, `cdf-implementation`, `cdf-orchestration`, `cdf-planning`, `cdf-requirements`, `cdf-ui-design`, `cdf-verification`.

Extras: `operator` → `cdf-model-calibration`; `learning` → `cdf-explain` and `cdf-teach`. Add `agents/openai.yaml` metadata with `policy.allow_implicit_invocation: false` for operator-only calibration (supported runtimes only); it remains manually invocable. For learning extras, normal intent-based activation is acceptable; `cdf-teach` already requires an explicit user-guided-learning request. Do not globally disable `cdf-requirements` because it must be available for ambiguous feature work.

## 10.7 Acceptance

1. CDF_20 core default advertises exactly 12 primary skill names, and no `delivery` legacy name.
2. A role-assigned worker can use selected primary skill(s) without loading all 12 bodies.
3. Subskill ID never becomes a claimed installed skill merely because present in registry.
4. Model calibration never runs implicitly as part of ordinary code task or install.
5. No root AGENTS content duplicates the full requirement, verification or orchestration procedural text.
6. Positive/negative activation runs observe appropriate skill loads when runtime exposes them; otherwise report unobserved, not passed.


---

# Implementation handoff

# Handoff to Codex: implement CDF 2.0 in controlled PRs

You are implementing an approved architectural migration, not designing a new one. Read `README.md`, `docs/00-decisions-and-system-boundaries.md`, `docs/07-migration-and-implementation.md` and **only the phase-relevant** deep specification. Read companion `CDF_2_0_SKILL_SPEC.md`/Skill Pack for actual primary skills; do not invent alternative names or replace them without demonstrated evaluation evidence.

**Baseline:** CDF v0.6.0 at `3ff534627e8b10de3dba2c6443855e870567ef84`. Confirm current working tree and HEAD; if they differ, inspect changes and preserve them. Do not modify user's installed global Codex config or ordinary app code during installer tests. Do not install third-party binaries or execute unreviewed community scripts.

**Work order:** PR-00 baseline/evals skeleton → PR-01 selected skills → PR-02 role TOMLs → PR-03 readiness/orchestration → PR-04 core installer → PR-05 safe lifecycle/legacy report → PR-06 model policy → PR-07 agent evaluations → PR-08 cleanup/release. Keep scope one PR at a time; each phase has explicit acceptance in `docs/07` and `tests/ACCEPTANCE-MATRIX.md`. Staged deployment and release require authorization.

**Core choices you must preserve:** one root agent by default; material user decisions before dependent edits; 12 core CDF skills, 1 operator and 2 learning optional; built-in worker/explorer; custom `cdf_reviewer`, `cdf_diagnostician` without pinned models; high-risk independent review or blocked status; no network/model call during core installation; user-owned files never overwritten; manifest+journal crash recovery; manual-only v0.6 migration for v2.0.0; optional Codebase Memory; no assumed Plus token conversion.

**Before coding:** check relevant existing implementation/tests and confirm the request includes a particular PR phase. Identify only **new material ambiguities** not settled by these documents; do not re-ask routine design decisions. If a source implementation differs, cite it and propose the least disruptive migration, not an unapproved redesign.

**After coding:** show changed paths, diff summary, exact commands and fresh outputs, failed/unavailable checks, review status and any remaining scope. Do not claim full CDF 2.0 success until real runtime tests and release gates pass. No staging/commit/push unless authorized.
