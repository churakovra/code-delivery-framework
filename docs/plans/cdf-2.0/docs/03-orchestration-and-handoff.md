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
