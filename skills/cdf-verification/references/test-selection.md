# Claim-to-evidence map

Use cdf-testing for designing, changing or removing tests. Verification owns authoritative commands, fresh output, environment, revision and evidence gaps.

| Claim | Credible evidence |
| --- | --- |
| Pure transformation | Focused unit results |
| HTTP/auth contract | Real request path with realistic dependencies |
| Database uniqueness/transaction | Real database constraints and transaction results |
| Event retries/recovery | Durable state, claims, retry timing and adapter boundary |
| External provider | Local transport tests establish only the local contract; live behavior needs live evidence |
| UI journey | Actual interaction and rendered evidence appropriate to the claim |
| Documentation | Relevant path/link/command check |

Use AC → changed path → check → observed result → gap for consequential claims. A screenshot cannot establish usability; a mocked client cannot establish database behavior. Preserve failed and successful retry results and investigate intermittency. Missing browser evidence limits visual claims; missing database safety evidence can block a migration. Do not run unrelated suites for a trivial change.
