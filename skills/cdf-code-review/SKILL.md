---
name: cdf-code-review
description: Review the actual diff or change for concrete correctness, contracts, security, regressions and missing tests with prioritized, reproducible findings. Use for requested reviews and risk-based independent reviews; not for speculative style audits.
---
# Change review

## Independence and scope
Establish exact baseline, branch/commit/PR or working-tree diff, acceptance and change ownership. Independent review must be done by a separate actor/context that did not implement the changes. A master self-check is valuable but must not be called independent.

## Method
1. Inspect actual changed code, surrounding callers, contracts, tests and relevant history. Challenge whether reported tests exercise affected production behavior.
2. Trace high-risk paths: authorization, monetary/data integrity, migrations, concurrency, secret handling, external side effects, serialization and failure recovery as applicable. Do not infer risk from line count alone.
3. For every finding include severity, actual file/line or symbol, triggering scenario, consequence and minimum actionable correction. Prefer correctness and regression defects over opinions about naming or style.
4. Validate potential findings against source; explicitly distinguish plausible concern from demonstrated defect. Do not rubber-stamp automated output or invent vulnerabilities.
5. Review substantive repairs on the updated diff. Keep reviewer read-only; return problems to owner for fixes.

## Exit
Concise findings in severity order, inspected scope, test-evidence gaps, and limitations. Zero findings does not equal proof of correctness.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `trailofbits-differential-review`: high-risk security-sensitive diffs or critical regressions; its default report/agent workflow must be scoped and may be tool-dependent.
- `superpowers-requesting-review`: coordinating a significant independent review handoff.
- `wsh-multi-reviewer`: exceptional complex reviews where independent perspectives warrant extra cost.
Fallback: the targeted diff/contract/failure-path review above.
