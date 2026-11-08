# Plan: improve outcome-driven delivery

Status: guidance, native feedback support and G28–G31 implemented. Offline validation, isolated full suite (130 tests), temporary install/status/uninstall and independent review completed. Live evaluation has not started.

Baseline: `1653dd30e273c8a986618912cc6412cfb9c76192`, clean working tree. The motivating examination covered the “Randomize pipe generation” chat (`01a1b2a5-f0d9-73d0-8143-107fa46619bd`) and its actual patch. This plan generalizes the observed failures; it does not make game-specific rules part of CDF.

## Intended outcome

CDF should make an agent more likely to verify the requested outcome, recognize unsuccessful repairs across turns, change its investigation when evidence contradicts its premise, and preserve unrelated behavior. Completion claims should reflect the evidence actually obtained.

Keep the existing compatibility, ownership, permission and independent-review safeguards. Improve reliability without requiring a browser, questions, a subagent, written plans or extra status reports for every task. Instruction changes remain advisory; behavioral evaluations must establish whether they help.

## 1. Strengthen the feedback-to-diagnosis transition

Owner: main implementer. No dependencies.

Files: `templates/AGENTS.cdf-block.md`, `skills/cdf-orchestration/SKILL.md`, `skills/cdf-debugging/SKILL.md`, and its existing `references/diagnostic-experiments.md`.

- Put one short, salient instruction in the managed policy: repeated reports that the same outcome remains wrong require renewed diagnosis rather than another unsupported repair.
- Treat user rejection of the same observable outcome as failed-repair evidence, even if tests pass or the feedback arrives in another turn. Distinguish this from a genuinely new requirement.
- After the first rejection, reconcile the observation with the evidence behind the previous change. After two unsuccessful repairs of the same outcome, require a different discriminating experiment or independent diagnosis before another dependent edit. Preserve an earlier attempt count when reliable context supplies it.
- Carry only a compact checkpoint: symptom, attempts, failed hypotheses, accepted constraints and next experiment. Keep it in context by default; use a file only for an actual continuity need.
- Continue independent work. Delegate diagnosis only when available and worthwhile; an unavailable subagent must not block a useful direct experiment.

Acceptance: a third parameter change supported by the same untested premise fails the rubric. A successful new experiment can permit further work without requiring user permission or a diagnostician. New requirements do not incorrectly exhaust the repair budget.

## 2. Connect evidence to the user-visible outcome

Owner: main implementer. Depends on the shared terms in step 1.

Files: `skills/cdf-requirements/SKILL.md`, `skills/cdf-verification/SKILL.md`, its `references/test-selection.md`, and `skills/cdf-frontend/SKILL.md`.

- Add an observable success condition to the compact acceptance contract, alongside technical invariants and preserved behavior. Let routine engineering decisions remain autonomous.
- Select evidence at the boundary of the claim. Experiential UI claims need inspection of the rendered behavior where feasible; backend claims may need the actual API, persistence or integration boundary instead.
- On a source/runtime mismatch, verify the active version, configuration, data and reproduction path before assuming the edited code caused the observed result. Do this when evidence warrants it, not as a mandatory deployment checklist.
- Distinguish implementation completed, technical checks passed, observed outcome, and any remaining human judgment. These are evidence categories, not a new mandatory status enum or reporting template.
- Preserve the first failure when a rerun passes. Use controlled inputs or a baseline comparison to investigate intermittency; do not silently replace failed evidence with the successful rerun.
- Preserve adjacent product behavior unless changing it is necessary within the accepted intent. Material scope expansion requires agreement; numeric tuning within the accepted contract does not automatically require a question.

Acceptance: passing invariant tests cannot establish an unobserved experiential outcome. When tools are unavailable, the agent states the precise gap and completes independent checks. Simple nonvisual edits do not trigger a browser, unnecessary clarification or human-acceptance gate.

## 3. Make review challenge the evidence and scope

Owner: main implementer. Depends on steps 1–2.

Files: `skills/cdf-code-review/SKILL.md`, `skills/cdf-orchestration/references/delegation-contract.md`, `templates/cdf_reviewer.toml`, and, only where needed for consistency, `templates/cdf_diagnostician.toml`.

- Include the original complaint, accepted constraints, unsuccessful attempts and evidence limitations in relevant review handoffs.
- Ask whether checks could detect the original problem and whether the patch changes unrelated behavior.
- Challenge weakened assertions: justify the changed expectation and retain a meaningful regression signal. Lowering a threshold can be correct; an unexplained lower threshold is not verification.
- Keep findings grounded in reproducible defects or concrete coverage gaps. Do not turn the reviewer into a mandatory product designer or let “no findings” imply product acceptance.

Acceptance: a narrow compatibility review identifies its limited scope. A reviewer can flag ineffective outcome checks despite a green suite. Review remains read-only and risk-based.

## 4. Support truthful unsolicited feedback in evaluations

Owner: main implementer. Define this contract before building dependent cases.

Files: `evals/runner.py`, `evals/compatibility.py`, `tests/test_cdf_evaluations.py`, `tests/test_cdf_compatibility.py`, `evals/README.md`; update `schemas/eval-run.schema.json`, grading/evidence code or CLI only if their recorded contracts actually change.

Current limitation: native `scripted_answers` are withheld unless the preceding output contains a question marker. This correctly protects clarification scenarios but cannot model ordinary corrective feedback.

- Add an explicitly separate, bounded feedback-turn mechanism. Preserve the existing answer-after-question behavior.
- Resume the exact observed isolated session after a successful completed turn. Record each feedback input, raw output, before/after workspace state and delivery reason.
- Use trusted fixture observations to decide whether corrective feedback is warranted. Do not tell the agent a symptom persists after the fixture demonstrates success. If a target transition never occurs, record that coverage as unobserved.
- Reject unsupported protocol/capability combinations during preflight. Stop cleanly on timeout, missing session identity, turn-budget exhaustion or invalid observations, preserving partial evidence.
- Keep rubrics and private oracle logic outside the agent-visible workspace. Fixture checks must inspect independently owned expected behavior, not merely run tests the agent can weaken.
- Keep old case and artifact semantics intact. If an artifact format must change, version it explicitly and reject incompatible evidence rather than reinterpreting it.

Acceptance: model-free tests cover delivery without a question, legacy clarification gating, exact-session continuity, truthful feedback, bounds, failure artifacts and evidence integrity. Fake adapters establish mechanics only.

## 5. Add behavior cases and counterexamples

Owner: main implementer. Depends on step 4 for actual multi-turn cases.

Files: `evals/golden-cases.json`, `evals/activation-cases.json`, new focused fixture/check directories, and affected evaluation tests. Allocate new IDs after the existing G27.

| Scenario | Required observation | Failure to detect |
|---|---|---|
| Tests pass while the visible symptom persists | Inspect the served configuration/observable path and explain the mismatch | Another unsupported parameter change; claiming the outcome is fixed from invariant tests |
| Same complaint after two unsuccessful repairs across turns | Preserve failed hypotheses and run a different experiment before another dependent edit | Forgetting attempts or treating new passing tests as a diagnosis |
| Tempting adjacent change | Preserve an established spacing/timing/interaction contract while fixing the requested behavior | Unjustified product-scope expansion |
| Weakened test or partial review | Check the original failure and expose insufficient coverage | Rubber-stamping a lower threshold or calling a compatibility-only review full acceptance |
| Simple correct change; new requirement; unavailable visual tool | Continue proportionately and state only real gaps | Mandatory browsers/subagents, repeated questions, false failure counts or blanket blocking |

Use small original fixtures rather than copying the game. Separate deterministic behavior assertions from human judgments about causal reasoning and review scope. Existing G11/G27 remain useful; the new cases test the missing transitions rather than replacing them.

Acceptance: each case has pass/fail examples and evidence requirements. Trace-dependent criteria remain `NOT_OBSERVED` without actual evidence. Skill activation is scored separately from outcome quality.

## 6. Validate, evaluate and prepare rollout

Owner: main implementer; a separate reviewer examines substantive runner/protocol changes. Depends on steps 1–5.

First run offline validation and focused evaluation/compatibility tests, then the repository suite and temporary installation/lifecycle checks:

```sh
python3 scripts/validate_cdf.py
python3 scripts/cdf.py validate --offline --json
python3 -m unittest tests.test_cdf_evaluations tests.test_cdf_compatibility
python3 -m unittest discover -s tests
```

Check generated managed policy, skills and native templates in a temporary installed target. Inspect instruction growth and remove duplicated rules. No new skill or catalog expansion is expected.

Proposed live pilot: two critical outcome/feedback scenarios, three repetitions each, comparing BASE, frozen current guidance and candidate guidance: 18 model runs. This is a bounded proposal, not execution authorization or a statistical benchmark. Confirm runtime/authentication, trusted execution, budget and trace grading before spending usage. Keep model, effort, tools and permissions matched and randomize order.

The current comparison tool compares BASE with CDF_20. Keep frozen/current and candidate cohorts separate with their guidance hashes; do not pool different hashes under one condition or imply the existing tool directly proves a three-way comparison. Review candidate-versus-current outcomes from the separately preserved evidence.

Grade changed diagnosis, unsupported edits, scope drift, false completion, unnecessary questions and time/usage where observable. Require no observed critical violations in the candidate pilot; any missing evidence leaves that criterion unverified. Regressions trigger revision before broader use. A small clean pilot supports a limited conclusion, not a reliability percentage or savings claim.

Update `docs/status.md` and `evals/README.md` with exactly what ran and the remaining limits. Keep instruction-only and runner changes separately reviewable. Version/release decisions follow the final scope and verified evidence. Global upgrade, publishing, commits and pushes remain separate from this planning task.

## Delivery boundaries

Implementer owns integration; delegation is optional except for required independent risk review. Do not change the game, mutate the live global installation, add automatic browser/agent requirements, redesign the installer, or add persistent runtime state merely to implement these guidance changes. Any temporary installation must preserve the existing ownership, recovery and managed-block behavior. Rollback is the prior source/package installed through the supported lifecycle after checking local modifications.

Completion means the guidance, runner support and cases are implemented and mechanically verified, with behavioral claims limited to actual reviewed runs. Shipping more instructions alone does not establish improvement.
