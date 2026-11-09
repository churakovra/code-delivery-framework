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
