# CDF 2.0 implementation status

Updated 2026-11-06. The follow-up installer, scoring, journal-validation and scenario-coverage repairs are implemented; deterministic checks and live acceptance are reported separately. This remains **1.0.0**, not a released or fully runtime-evaluated CDF2. The supplied proposal is the design record; current executable code and `skills/cdf-*/` are the implementation source. See [completion plan](COMPLETION_PLAN.md).

| Phase | Repository implementation | Remaining acceptance |
| --- | --- | --- |
| PR-00 | Pinned 0.6 tree, planning archive identity and 137 passing baseline tests recorded | None for baseline capture |
| PR-01 | 12 core + 3 optional skills, 9 references, 31 optional candidates, executable positive/negative activation pairs | Live skill-selection observations; separate upstream verification before community installation |
| PR-02 | Two native agent templates without model pins; earlier isolated discovery verified 12 core skill names | Actual custom-agent launch/behavior evidence |
| PR-03 | Readiness and risk gates, bounded handoffs, two-worker default and operator-profile rules | Live readiness/review/continuity scenarios |
| PR-04/05 | Offline lifecycle, ownership, journal and directory cleanup/recovery, structured status, migration report; additive `.codex/.gitignore` managed block and `.codex/cdf-cleanup.json` intent | Real power-loss and additional-platform validation; tracked-secret inspection/remediation is manual and Git index is never changed |
| PR-06 | Operator policy loader, profile worker/review decisions, fallback enforcement, advisory inspection CLI and runtime-aware model-pair resolver | Actual runtime model/effort confirmation and calibration; no allowance savings measured |
| PR-07 | 27 golden cases, 24 executable activation cases, 15 behavioral checks, isolated Git baselines, native scripted resume, external control protocol, complete hash-consistency manifests, re-derived usage, evidence-bound grading/comparison and critical gate | Authenticated live runs, real adapter-control observations, comparable runtime/tool evidence and human grading; installed-system gate requires actual integration setup evidence |
| PR-08 | Development docs and manual breaking-migration guidance | Live acceptance and explicit release authorization; legacy pruning deferred |

## Earlier audit corrections

| Finding | Implemented correction and checks |
| --- | --- |
| False PASS / unbound comparison input | Comparator validates every record, binds summary/run/check/fixture/grade artifacts, rejects unknown-as-pass and detects changed evidence; adversarial comparator tests |
| Missing comparative analysis | Matching case/fixture/Git identity and reviewer-attested runtime/model/effort/tool/permission parity; class/risk paired comparisons against BASE and CDF_06; explicit insufficient-data uncertainty and observed-token-only resource summaries |
| Incomplete release gate | Critical CDF_20 failures fail the gate; missing or unobserved evidence blocks it. Observed baseline failures may represent candidate improvement. G09 requires available-reviewer completion evidence, G13 requests reviewer unavailable |
| Metadata-only activation scenarios | A01P through A12N are selectable runner cases covering each core skill positively and negatively |
| Weak fixtures / no continuity setup | G10 has at least 150 removable lines; G07 exercises the actual component using a DOM test double; G08 checks real HTTP GET /export and varied responses and rejects hardcoded output; G09/G13 have explicit availability controls; G16 requires prior turns and compaction; G19 supplies answers after a question |
| Missing dialogue adapter | Native Codex resume uses the observed exact thread UUID, withholds answers without a question marker, and records per-turn inputs and pre-answer snapshots. Fake-CLI tests cover mechanics; unsupported runtime controls fail preflight |
| Unused operator settings | Installed orchestration guidance consumes explicitly selected profile budgets/review/fallback rules. The pure helpers and `scripts/inspect_cdf_policy.py` consume those fields without launching agents or changing config |
| Directory cleanup / recovery contracts | Manifest/journal record created directories; a durable `.cdf-cleanup.json` intent supports final cleanup. Only recorded empty directories are removed. Recovery conflicts retain exit 3 and status reports affected paths |
| Legacy external MCP / test isolation | Migration report validates/reports external MCP metadata without following external paths. Installer tests isolate HOME and CODEX_HOME |

## Earlier verification (before follow-up repairs)

- `python3 -m unittest discover -s tests` — **228 tests passed in 18.374 seconds** after completion repairs.
- `python3 scripts/cdf.py validate --offline --json` — passed: 12 core, 3 optional, 31 candidates and 2 native templates. No network/model call.
- `python3 scripts/validate_cdf.py` — passed.
- `git diff --check` — passed.
- Independent installer/policy review: 59 focused tests passed; no outstanding actionable findings in that scope.
- Independent final evaluation re-review: 32 focused tests passed; both reported G08/G09 gaps rechecked with no further actionable findings.

Earlier 137/186/194/226 passing counts are historical checkpoints, superseded by this completion run. `discovery-evidence.json` records the earlier isolated skills/list observation, not a fresh claim about live task behavior. `lifecycle-evidence.json` records the earlier temporary project/global smoke; the fresh suite additionally covers directory ownership and interrupted cleanup.

## Explicit runtime gates and limitations

No live model benchmark, subscription measurement, user-global migration, repository commit, push, publication or release has been performed. The evaluation baseline is the pinned repository source, not the user's installed CDF.

The planned 12-run smoke is G01/G02/G09/G13 across BASE/CDF_06/CDF_20, followed by evidence-backed grading. Test homes inherit no credentials. G09/G13 require a controlled external adapter for reviewer availability; the built-in Codex adapter rejects these controls. G16 likewise needs an adapter capable of real prior turns and compaction. Capability declarations and review-completed events are adapter-reported claims: actual behavior and independence still need human evidence review. Native scripted resume is implemented and tested with fake CLI events, not a live model. Its question-mark detector can be inconclusive and fails closed.

G07 uses a DOM test double; real-browser accessibility and keyboard acceptance remain unverified. Generated-code behavior checks require an external OS sandbox for untrusted runs; temporary homes alone are not a security boundary. Codebase Memory is not installed by the harness, so runtime parity must be established rather than assumed. Unknown quality/coordination metrics remain null; available timestamps and documented command/token events do not measure Plus allowance.

A crash between creating a directory and recording ownership can leave an empty directory; recovery deliberately avoids deleting anything it cannot prove CDF created. Actual power-loss durability and platforms beyond the current host remain unverified. Older manifests without directory ownership records are handled conservatively.

These acceptance gates still block release and legacy pruning. Follow-up repairs have focused verification and independent review; these do not satisfy the live gates. They are not represented as passing model evaluations by the deterministic test suite.


## Follow-up conformance evidence (2026-11-06)

- Evaluation schema/rubric version 2 separates shared behavioral results from CDF2 activation. Baselines can pass without CDF2 skills; activation-only failure cannot count as a behavioral win. Applicable CDF2 activation failures still fail the critical release gate. Earlier run/grade artifacts must be rerun, not silently reinterpreted.
- Recovery journals undergo bundled schema validation before processing recorded paths. Malformed records, including boolean schema values, return recovery-required and preserve target bytes/modes; a restored valid journal recovers.
- G20–G27 explicitly cover grouped decisions, budget interruption, forbidden writes, disjoint workers, child escalation, ownership violations, changed MCP indexes and diagnosis handoffs. G23 has a real two-module check; G22/G25 enforce unchanged fixture snapshots. External runtime controls require declared support and human evidence of actual enactment.
- Full suite: `python3 -m unittest discover -s tests` — **233 tests passed in 18.909 seconds** after follow-up repairs.
- Focused installer suite: 41 passed. Focused evaluation suite: 36 passed. Contract suite: 19 passed. Independent review found no actionable defects in the journal or evaluation repairs.
- Offline/source/archived-blueprint validation and whitespace checks passed. The archived blueprint still describes its original 18 cases; executable golden scenarios now number 27.

No live G01/G02/G09/G13 model runs, real permission-control validation, external dialogue adapter, independent live trace review, savings measurement, release, legacy pruning or commit occurred. Source provenance inherited from the proposal remains separately unverified upstream.


## Review upgrade gates

- Installer lifecycle: use temporary targets; inspect additive `.codex/.gitignore` preservation, `.codex/cdf-cleanup.json` recovery, missing-path uninstall convergence, modified-skill release behavior and preservation of AGENTS/backups. Existing tracked secrets require manual inspection/remediation; no automatic untracking occurs. POSIX mutations are gated early; Windows support is not claimed.
- Evaluation evidence: retain complete raw artifacts and consistency manifests; verify usage by re-deriving it from trace. Hashes establish consistency, not authenticity. Malformed evidence manifests fail with controlled errors. Early runner failures retain comparable error records; late failures after an immutable record stop without emitting a contradictory aggregate.
- Comparison: standardized mode requires equal attested tools; installed-system mode allows condition-specific tools but its gate is currently disabled pending support for verifying actual integration setup.
- Runtime acceptance: actual Codex version/resume compatibility, live G01/G02/G09/G13 runs, external dialogue controls, human independent trace review, and savings measurement remain open. CI is configured for Ubuntu/macOS and Python 3.11/3.13 with Node 22, but remote workflow execution and branch protection are unverified/unconfigured.
- Keep release and legacy pruning blocked until live gates and explicit release authorization are complete. Process execution, evidence and bundle inventory have separate modules; broader installer decomposition remains deferred until the behavior stabilizes.

## Verified review upgrades (2026-11-06)

- `python3 -m unittest discover -s tests` — **258 tests passed in 20.585 seconds** on the current macOS host. This supersedes the historical 233-test checkpoint above; these are model-free tests.
- `python3 scripts/validate_cdf.py`, `python3 scripts/cdf.py validate --offline --json`, `python3 docs/plans/cdf-2.0/tests/validate_blueprint.py`, and `git diff --check` passed. The archived blueprint still contains its original 18 cases.
- Independent review found dry-run/no-op side effects and inconsistent late-failure evidence. Both were repaired with regression coverage; independent re-review found no remaining actionable defects in its scoped inspection of the integrated patch.
- Regression coverage includes staging during an interrupted transaction, modified-skill ownership release, missing-file uninstall convergence, reversed markers, invalid policy tables, raw-trace/usage tampering, malformed evidence, early/late runner failures, and refusal before execution when trust or prerequisites are missing.
- No live model run, real sandbox verification, remote CI run, branch protection change, commit, release or publication occurred. A controlled dialogue adapter, verified isolation for untrusted code, actual version/control observations and independent live trace review remain prerequisites for runtime acceptance.
