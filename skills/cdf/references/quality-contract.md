# Quality and acceptance

Use the existing implementation when its ownership, compatibility, lifetime and failure semantics fit. Explain a concrete mismatch before adding an abstraction. Preserve permissions, data invariants, errors, resource cleanup and adjacent behavior. Prefer readable local changes over unrelated refactoring.

For nontrivial changes maintain this compact mapping in context:

`AC → expected observable behavior → changed implementation path → authoritative check → observed result → gap`.

Choose checks at the claimed boundary: a mock does not establish real DB uniqueness; a passing unit does not establish the active UI route. Include relevant adverse paths. Do not weaken assertions to obtain a pass. Use cdf-verification for actual commands, outputs and freshness; retain initial failures as well as successful reruns.

Review actual changed code and callers against both original accepted outcome and engineering invariants. High risk requires an independent actor/context; self-review is not independent. Medium risk warrants review for changed shared contracts, weak failure evidence or uncertain rollback. Read each finding against source before fixing; reject an incompatible refactor with evidence. Repair blocking defects, rerun affected checks and reassess the updated diff with the reviewer.

## Capability degradation

| Capability | Missing capability means |
| --- | --- |
| optional | Use local fallback; continue (for example an external research skill) |
| required_for_claim | Narrow the claim and report PARTIAL (for example browser evidence for a visual claim) |
| required_for_safe_action | BLOCKED for dependent unsafe work (for example DB access needed to validate a destructive migration) |

An unavailable required reviewer permits patch preparation and checks but blocks fully reviewed readiness. It does not make self-review independent. Do not impose a browser check on documentation or a DB check on unrelated code.

COMPLETE means all acceptance required for the stated result and required review are observed, with no material decision unresolved. PARTIAL names unmet acceptance/evidence and its practical risk. BLOCKED names the missing decision, permission or capability needed to proceed safely; independent work can continue. These are user-facing guidance, not replacements for optional task-state schema enums. No mandatory JSON artifact for a tiny change.

## Outcome evidence

Activity evidence records what the agent did; outcome evidence establishes what the user actually received. A successful intermediate experiment does not establish completion of the full accepted scope.

| Activity evidence | Outcome evidence |
| --- | --- |
| Endpoint written | Real request performs the required action |
| Unit test passed | Original defect repaired on the active execution path |
| HTML created | Requested user flow works in the opened interface |
| Components written | Required functionality is available to the user |
| Plan executed | All required outcomes are achieved |

Check the requested artifact or operation itself before reporting completion. For applicable claims, distinguish semantic/product correctness, functional/runtime behavior and visual/experience quality. Each can be OBSERVED_PASS, OBSERVED_FAIL, NOT_OBSERVED or NOT_APPLICABLE; evidence in one layer does not establish another.

| Claim | Credible boundary | Insufficient proxy |
| --- | --- | --- |
| Interactive process explorer | Source-backed transitions, drilldown and Back in the opened artifact | Summary, card count or invented arrows |
| Usable visual direction | Rendered representative viewports, concrete critique and applicable user feedback | DOM counts, screenshot existence or design skill name |
| Host displays an icon | Requested surface in the actual host version | Valid SVG/YAML or discovery path |
| Original defect repaired | Original reproduction on the active route/version plus regressions | Unrelated green unit tests |

Return the artifact path when an artifact is requested. Missing required runtime or visual evidence leaves PARTIAL; do not require subjective visual acceptance for a nonvisual change. A safe implementation can be ready mechanically while behavioral improvement remains unproven.
