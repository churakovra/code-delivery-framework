# CDF 2.0 evaluation fixtures

These cases are unexecuted agent evaluations. The legacy `scripts/run_evaluation.py` remains available for the v0.6 bounded counter exercise. Each selected condition uses a new temporary project and home. A deterministic fixture Git commit is created independently for each condition. `BASE` has only the fixture; `CDF_06` is built from pinned commit `3ff534627e8b10de3dba2c6443855e870567ef84`; `CDF_20` uses the offline installer in the disposable project. No Codebase Memory or community skills are installed. Runtime parity with a typical v0.6 installation is not established.

`golden-cases.json` contains 27 scenarios, including a clarification-and-resume case. `activation-cases.json` retains the original cases and adds executable positive/negative pairs for the 12 core skills (`A01P` through `A12N`). G20–G27 add grouped decisions, budget interruption, denied writes, parallel workers, child escalation, ownership violations, changed indexes and diagnosis handoffs. G23 has a deterministic integration check; G22 and G25 compare unchanged workspace snapshots. The others require human trace review. G21–G27 require external controls declared by the adapter; declaration is not evidence the control actually occurred. Each case records desired final state, review expectation, skill triggers and stop conditions. A skill trigger is a test expectation, never proof of an observed skill load.

Run a read-only preflight first:

```sh
python3 scripts/run_cdf_evaluation.py --case G01 --adapter /absolute/path/to/adapter --preflight
```

An external adapter starts in the fixture directory. `HOME`, `CODEX_HOME`, and `XDG_CONFIG_HOME` point to a new empty temporary home; unrelated environment variables and credentials are not passed. Stdout/stderr are retained unmodified: keep secrets out of fixtures, adapter output and annotations. A separate process executes fixture checks after the adapter exits, which executes the changed fixture code. **Temporary directories are not an operating-system sandbox**. Run untrusted adapters and generated code under an external sandbox. The built-in Codex adapter requests workspace-write sandboxing for Codex commands, not for the subsequent fixture check.

The default `prompt-v1` protocol supplies the initial prompt as UTF-8 text. Scripted answers can use the built-in Codex resume path or a separately supplied external dialogue adapter. Prior session messages or runtime controls require an external adapter and capability declaration:

```sh
python3 scripts/run_cdf_evaluation.py --case G19 --adapter /absolute/path/to/dialogue-adapter \
  --adapter-protocol json-dialogue-v1 --adapter-capabilities /path/to/capabilities.json \
  --preflight
```

See `adapter-capabilities.example.json`. The operator must declare `multi_turn: true` for prior messages or scripted answers, and list each supported runtime control. The adapter receives a single JSON object with `schema: 1`, `prompt`, `scripted_answers`, `prelude_messages`, and `runtime_controls`. It must send prior messages as real earlier turns, apply the requested control, send `prompt` as the current user message and provide each answer only after the agent asks. It must preserve the interaction and control evidence in stdout. Answers, prior messages, and controls are separate from the current prompt; grading rubrics are never supplied. A capability declaration is an **operator assertion**, not verified execution. Review the actual trace before grading. G09 requests reviewer availability and a completed independent review; G13 requests reviewer unavailability and a blocked result. G16 requests compaction after earlier turns, and G19 tests clarification followed by an answer. The built-in Codex adapter rejects runtime-control and compaction scenarios in preflight. No external dialogue adapter is shipped.

For scripted answers without runtime controls, the built-in Codex adapter starts a non-ephemeral session in the isolated home, extracts its exact `thread.started` UUID, and resumes that thread for each answer. It sends an answer only after an `agent_message` event contains a question mark; absent that conservative marker, it records `RUNNER_ERROR` and withholds the answer. A question without a question mark can therefore be unrecognized, and actual dialogue semantics require human trace review. Per-turn raw output, answer inputs, and the workspace snapshot and diff before each answer are retained. This protocol is covered with fake adapters; it has not been tested against a live model.

Actual adapter execution requires explicit opt-in and a new output directory:

```sh
python3 scripts/run_cdf_evaluation.py --case G01 --adapter /absolute/path/to/adapter \
  --allow-model-runs --output /tmp/cdf-g01
python3 scripts/compare_eval_runs.py /tmp/cdf-g01 --csv /tmp/cdf-g01-summary.csv
```

For Codex CLI use `--adapter-kind codex`: it probes `--version`, then uses `codex exec --json` with an isolated empty Codex home. No credentials are copied, so authentication may be unavailable. External adapters and checks can execute code and consume usage; the switch is required even for a fake test adapter. Output directories and CSV paths must not already exist. `--conditions BASE CDF_06 CDF_20` selects conditions; `--seed` controls randomized order; `--timeout` bounds each process. `--model` and `--effort` request a Codex candidate; the active pair remains unverified. Exit zero means the run had no deterministic failure, **not** that the evaluation passed.

The runner records process timestamps, raw traces, workspace diff, initial Git identity, file/permission metadata, and fixture and installed-guidance hashes. The G14 dirty-tree case preserves an unrelated modified file; all conditions record Git HEAD, branch and staged-diff changes. G07 executes the actual component against a small DOM test double and checks retry interaction and semantic attributes; it does not establish browser accessibility. G08 requires the UI's injected fetcher to make a real `GET /export` request to the Python HTTP handler through a local socket pair and map varied response IDs; no port is bound. Both checks require Node.js.

Only deterministic checks are scored automatically. Review independence, skill activation, clarification, prohibitions, and trace-dependent criteria remain `NOT_OBSERVED` until reviewed. Timeout or process failure is `RUNNER_ERROR`, and a failed deterministic check is `FAIL`. `metrics.json` uses null for unobserved quality/coordination metrics, with documented completed-command events counted only when present. The runner extracts input/output and, when present, cached input tokens from valid Codex `turn.completed` events. These figures cover only reported trace turns and do not establish subscription consumption. Model, effort, agent availability and skill discovery remain unverified by the runner.

For a reviewed result, copy `grading.example.json` outside the output and provide one assessment per applicable assertion. Rubric version 2 separates shared behavior from CDF2 skill activation. BASE and CDF_06 have no CDF2 activation assertions; for CDF_20 include each activation assertion from the case. Schema 1 run and grading artifacts are rejected; re-run them rather than silently reinterpreting them. For negative assertions, `PASS` means the prohibited behavior did not occur. Every pass or fail needs a reason and one or more references to UTF-8 artifacts with `path`, `start_line`, and `end_line`; use `NOT_OBSERVED` when evidence cannot establish the answer.

```sh
python3 -m evals.grade --run /tmp/cdf-g01/BASE --annotations /path/to/annotations.json
```

Grading writes new `grading.json` and `graded-run.json` without changing the original run. It records the reviewer and hashes each citation. Comparison verifies source record, environment, case and cited artifact hashes. It checks evidence locations and integrity, not whether the reviewer's interpretation is correct; human assessments are not automatic proofs.

To grade G09's `independent_review_completed` as `PASS`, cite both `final.diff` and a `stdout.ndjson` line containing an adapter event like `{"type":"cdf.review.completed","schema":1,"independent":true,"reviewer_id":"child-reviewer","scope":"authorization diff"}`. An event saying review is blocked does not satisfy this requirement. The event is an adapter-reported claim, not technical proof of independence: the human reviewer must check the actual review, actor, and diff in the trace. If the runtime cannot produce enough evidence, leave the assertion `NOT_OBSERVED`.

Comparison validates and binds every result to its run and fixture artifacts. It reports descriptive paired CDF 2.0 versus BASE and CDF 0.6 wins/losses/ties by case class and risk only for identical fixture/case/Git baselines with matching reviewer-attested runtime, model, effort, tools and permissions. `--parity-evidence /path/to/parity.json` supplies attestations in the form of `parity-evidence.example.json`; citation hashes must match actual files. Runtime attestations are human judgments, not automatic discovery. Inconsistent guidance hashes within a framework condition prevent matched status. Unmatched or unobserved runs are excluded from paired counts. The evaluation release gate requires matched G01, G02, G09 and G13 conditions, passing CDF_20 outcomes, and observed BASE/CDF_06 outcomes. Paired wins use behavioral results only. A baseline behavioral failure may be a comparative win; a CDF_20 critical behavioral or applicable activation failure fails the gate. Missing activation evidence blocks the gate. Missing or unobserved evidence blocks it. This gate does not substitute for installer, security or release review. `--require-release-gate` returns nonzero unless it passes. Counts are descriptive: small samples are labelled insufficient and no statistical confidence is claimed. Resource-normalized counts use only observed trace-token denominators and do not estimate subscription allowance.

The fixtures are not benchmark results. Automated trace interpretation remains limited, and no runtime can be claimed to support an external adapter's declared controls until evidence is inspected. Full model/tool parity, real model runs, browser accessibility, and human review remain open. Run `python3 -m unittest tests.test_cdf_evaluations` for model-free tests; those tests exercise mechanics rather than agent quality.

The external adapter control names `budget_interrupt`, `deny_workspace_writes`, `two_workers_available`, `inject_child_decision`, `inject_child_out_of_scope_edit`, `change_mcp_index`, and `inject_failed_repair_history` require the corresponding real runtime setup and trace evidence. A fake adapter can test protocol and checks but cannot establish that those controls occurred. G20 requires human review of grouped questions and preservation of the fixture.
