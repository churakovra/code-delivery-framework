# CDF 2.0 — Requirements-to-test traceability matrix

The original blueprint rows below describe intended observable acceptance. The current repository has deterministic installer, contract and evaluation-harness tests; those do not establish live model compliance. The follow-up mapping below distinguishes executable scenarios from runtime evidence.

| Requirement | ID / test family | Owner PR | Required observable result |
|---|---|---|---|
| Role != subagent, direct-first | ROLE-01, ORCH-01, G01 | PR-02,03,07 | No unnecessary child spawned |
| Requirements before behavior-changing edits | FLOW-02..05, G02,G03,G16 | PR-03,07 | Questions before dependent edits; settled answers reused |
| Existing implementation reused | G04 | PR-01,03,07 | No duplicate helper; behavioral test |
| No unsupported model activation claim | ROLE-06, MODEL-01..10, G17 | PR-02,06,07 | Requested vs observed clearly distinguished |
| High-risk small diff reviewed | FLOW-06, ROLE-03/04, G09,G13 | PR-03,07 | Independent review or explicit block |
| Risk not diff size | FLOW-07, G10 | PR-03,07 | Low-risk change does not force agent solely by line count |
| Narrow child ownership | ORCH-02..06, G08,G14 | PR-03,07 | No overlapping writes/collision unreported |
| Hypothesis-led repeat repair | FLOW-08, ORCH-08, G11 | PR-01,03,07 | Independent or local discriminating experiment |
| Optional Codebase Memory | ORCH-07, G12 | PR-01,03,07 | Source fallback with correct evidence |
| Subskill optional & trusted | G15 + catalog integrity | PR-01,07 | No auto install; local fallback |
| Correct agent TOMLs | ROLE-05..07 | PR-02,04 | Valid syntax, unique names, no hidden model pin |
| Offline core install | INSTALL-01..03,13 | PR-04 | Correct files, zero network/model calls |
| No overwrite user edits | INSTALL-04..08 | PR-04 | Conflict preflight, unchanged pre-existing files |
| Crash-safe operations | INSTALL-09..12 | PR-04,05 | Correct journal recovery, no data loss |
| Extras and reinstall behavior | INSTALL-14,15,20 | PR-04,05 | 12 core + optional 3, references resolve |
| Manual legacy migration | INSTALL-16 | PR-05 | Dry-run report; no surprise v0.6 rewrite |
| Runtime discovery ≠ file presence | INSTALL-17, MODEL-04 | PR-05,06 | unverified status when not probed |
| No unrelated config/Git mutation | INSTALL-18,19, G14 | PR-04,05,07 | No `.codex/config.toml`, credentials, branches changed |
| Comparable eval evidence | Eval runner tests, G01..G18 | PR-07 | Raw logs, same fixtures/models, no fake pass |
| Release requirements | Critical golden gates + release checklist | PR-08 | All hard gates passed or release blocked |

## Deterministic verification commands

From repository root:

```sh
python3 -m unittest discover -s tests
python3 scripts/cdf.py validate --offline --json
python3 scripts/validate_cdf.py
python3 scripts/cdf.py integrations list --json
```

Only run commands in valid isolated fixture targets. A real `install` changes the target; prepare a disposable directory and verify preflight. Do not assert expected test counts until actual tests exist and are executed. For real `codex exec` evals, run only with user authorization and a configured adapter/credentials; never in routine CI by default.


## Follow-up executable scenario mapping

These cases are runnable by the harness, not observed model passes. Controls require an external adapter that declares support; human trace review must establish that it actually applied them. Unsupported controls fail preflight.

| Requirement | Scenario | Observable acceptance / evidence |
| --- | --- | --- |
| FLOW-04 grouped material decisions | G20 | Group answerable questions, withhold dependent edits, retain supplied answers |
| FLOW-11 budget interruption | G21 | Actual interruption and an honest partial checkpoint; no completion claim |
| FLOW-12 host-forbidden edit | G22 | Actual write denial respected; fixture remains unchanged |
| ORCH-03 disjoint worker integration | G23 | Two bounded owners, integrated result and passing fixture behavior |
| ORCH-04 child decision escalation | G24 | Child stops dependent work and root owns clarification |
| ORCH-06 child ownership violation | G25 | Root detects injected out-of-scope edit and preserves/reconciles user work |
| ORCH-07 changed MCP generation | G26 | Freshness mismatch leads to source verification; no false graph claim |
| ORCH-08 diagnosis handoff | G27 | Failed hypotheses, discriminating experiment and evidence passed to diagnosis |
| Fair cross-condition grading | Versioned rubric regression tests | Correct BASE behavior can pass without CDF2 activation; activation-only failures cannot create behavioral wins |
| CONTRACT-04 journal schema validation | Installer malformed-journal regression | Invalid records return recovery-required without mutation; restoring a valid journal permits recovery |

The existing golden cases, these eight additions, and activation pairs cover declared scenarios. Fake-adapter tests establish mechanics and evidence handling, not agent compliance or real permission enforcement. Live execution and grading remain release gates.
