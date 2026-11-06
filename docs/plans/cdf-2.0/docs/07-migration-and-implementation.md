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
