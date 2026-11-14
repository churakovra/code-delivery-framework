---
name: cdf-code-review
description: Review the actual diff or change for concrete correctness, contracts, security, regressions and missing tests with prioritized, reproducible findings. Use for requested reviews and risk-based independent reviews; not for speculative style audits.
---
# Change review

## Independence and scope
Establish exact baseline, branch/commit/PR or working-tree diff, acceptance and change ownership. Independent review must be done by a separate actor/context that did not implement the changes. A master self-check is valuable but must not be called independent.

## Method
1. For structural changes, first compare the accepted solution with observed requirements and existing reuse contracts. Identify a concrete mismatch before endorsing additional infrastructure; a correct diff does not establish that its architecture is needed. Keep solution-quality evidence separate from implementation findings. Inspect actual changed code, surrounding callers, contracts, tests and relevant history. Use the original complaint, accepted constraints, unsuccessful attempts and evidence limits when relevant. Challenge whether reported tests detect the original problem and whether the patch changes unrelated behavior. Justify weakened assertions and check that a meaningful regression signal remains; lower thresholds can be valid but are not evidence by themselves.
2. For added or changed scripts, plugins, callbacks and other invoked components, trace the actual production caller. Check arguments, working directory, environment, inputs and exit/output semantics; verify that supporting tests exercise the same invocation contract. Trace high-risk paths: authorization, monetary/data integrity, migrations, concurrency, secret handling, external side effects, serialization and failure recovery as applicable. Do not infer risk from line count alone.
3. For every finding include severity, actual file/line or symbol, triggering scenario, consequence and minimum actionable correction. Prefer correctness and regression defects over opinions about naming or style.
4. Validate potential findings against source; explicitly distinguish plausible concern from demonstrated defect. Do not rubber-stamp automated output or invent vulnerabilities.
5. Review substantive repairs on the updated diff. Keep reviewer read-only; return problems to owner for fixes.

## Exit
Concise findings in severity order, inspected scope, test-evidence gaps, and limitations. Distinguish integration boundaries exercised from those only inspected; passing component tests do not establish integration correctness. Zero findings does not equal proof of correctness or product acceptance. A compatibility-only review must state that limit; report concrete coverage gaps without inventing product-design requirements.

Use two lenses: accepted outcome and preserved behavior; actual changed code, production callers and adverse paths. Classify findings as SPEC_GAP, DEFECT, EVIDENCE_GAP or NONBLOCKING alongside severity, location, trigger, consequence, minimum correction and proof/uncertainty. The author validates each finding before repairing it; review substantive fixes on the updated diff after relevant checks.

## Optional subskills
Resolve candidates through the bundled catalog only when needed. A portable plugin keeps it at `skills/cdf/subskills.catalog.json`; the legacy installer places it at `.codex/cdf/subskills.catalog.json`. Confirm native discovery and use the local fallback when absent; never install automatically.

- `trailofbits-differential-review`: high-risk security-sensitive diffs or critical regressions; its default report/agent workflow must be scoped and may be tool-dependent.
- `superpowers-requesting-review`: coordinating a significant independent review handoff.
- `wsh-multi-reviewer`: exceptional complex reviews where independent perspectives warrant extra cost.
Fallback: the targeted diff/contract/failure-path review above.

Report EVIDENCE_GAP when a claimed user-facing outcome has only proxy checks: for example, host icon rendering inferred from YAML or an explorer inferred from a summary. Name the missing runtime observation. Keep visual preference separate from correctness and security findings.
