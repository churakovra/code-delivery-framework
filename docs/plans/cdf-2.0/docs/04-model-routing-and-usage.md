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
