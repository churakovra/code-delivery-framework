---
name: cdf-verification
description: Verify an implementation or claim using fresh project-authoritative test, build, type, integration and behavior evidence. Use before declaring a code change complete or when asked to validate; no needless full-suite reruns.
---
# Evidence-based verification

1. Translate each acceptance criterion and changed contract into the smallest credible check at the boundary of the claim. Invariant tests alone do not establish an experiential outcome. Include failure and regression cases when relevant; use integration checks for persistent/external boundaries.
2. Discover authoritative commands from project tooling, CI and docs. Prefer the earliest check that could falsify the requested outcome at its actual boundary, then affected tests and appropriate type/lint/build checks. Before another broad suite, name the changed risk, relevant input or unresolved failure that makes the previous result insufficient; an unchanged diff alone is neither a reason to repeat nor proof that external inputs stayed valid. Preserve required checks and disclose the remaining remote boundary.
3. Read fresh output, exit code, environment and relevant revision. If a rerun passes, retain the original failure and investigate intermittency with controlled inputs or a baseline comparison. Distinguish checks that passed, failed, were skipped, or could not be run. A prior agent's summary is not raw evidence.
4. Check that an assertion could detect the claimed regression; avoid tests that only mirror the implementation. When appropriate, first see the test fail against the broken behavior.
5. For experiential UI claims, inspect rendered behavior where feasible; for API, persistence, compatibility or security claims, check the relevant integration boundary. When source and observed behavior disagree, verify the active version, configuration, data and reproduction path before further tuning. Do not impose browser checks on nonvisual work.
6. Report implementation, passed technical checks, observed outcome and remaining human judgment distinctly without a mandatory status template. Unavailable tools leave a precise evidence gap; continue independent checks.
7. Do not modify product code in a read-only verification assignment. Return failures to the implementer with a reproducible minimal report.

For nontrivial work, inspect the acceptance map: AC → behavior path → tested boundary → raw observed result → limitation. Include the original user complaint and preserved behavior. Classify an unavailable capability as optional (fallback), required for the claim (narrow it and report PARTIAL), or required for safe action (block dependent work). Do not count an unobserved integration or required review as passed.

## Reference
- `references/test-selection.md` for selecting unit/integration/contract/E2E layers.

## Optional subskills
Resolve candidates through the bundled catalog only when needed. The Codex plugin keeps it at `skills/cdf/subskills.catalog.json`. Confirm native discovery and use the local fallback when absent; never install automatically.

- `superpowers-verification-before-completion`: consequential completion claims with multiple checks or suspicious reports.
- `wsh-python-testing`: Python/pytest fixture, isolation or async test design.
- `superpowers-tdd`: when a reliable regression needs red/green evidence.
Fallback: test-to-claim mapping and fresh command evidence above.

For UI work, exercise one main journey and a relevant failure path on the active route; inspect representative desktop/mobile views when the claim requires them. Evaluate source-backed semantics, functional interaction and visual readability separately. Metadata validation does not prove a host renders an icon. A screenshot alone does not prove usability, and a unit test does not prove visual quality. If the boundary is unavailable, report NOT_OBSERVED and narrow readiness to PARTIAL rather than asserting success.
