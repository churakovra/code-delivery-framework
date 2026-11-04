---
name: model-routing
description: Compare available models and reasoning efforts across agent roles to find useful quality at the lowest practical usage or cost. Use when choosing or reviewing a role-to-model configuration.
---

## Scope and profile

Recommend for the user's actual roles, runtime, plan, workload, quality and risk requirements. Read [selection-profile.toml](references/selection-profile.toml) when present and use any supplied profile. Preserve explicit choices and constraints; treat earlier recommendations as hypotheses. If the profile is absent, label assumptions and ask only for missing information that could change the recommendation.

Optimize cost per successful task, including failed attempts, review, repairs, escalation, latency and repeated context. The cheapest call or strongest model is not necessarily the best value. Do not store dated rankings, prices or claims in the profile.

## Research

Identify the exact runtime, plan, available models and efforts, usage windows and active limits, preferring runtime views. Distinguish listed models from pairs confirmed selectable for each role; account for fixed assignments and role instructions. Include relevant older models and exclude unavailable ones.

Research current official provider model, product and plan documentation, plus independent comparisons such as Artificial Analysis when available. Follow relevant user-provided sources to their origin. Compare role-relevant scores, API prices, token use, latency and cost per task where reported; check dates, benchmark methods, task fit, versions and reasoning settings.

Separate verified facts, observations, proxies and inference. Identify missing comparisons for the exact pairs or workload. API prices and benchmark tokens do not directly measure subscription allowance; remaining account percentage alone does not establish per-task usage. Never invent rankings, savings or task counts.

## Compare configurations

For each role, identify its work, frequency, stakes, activation, context and observable quality threshold. Distinguish planning, implementation, QA, independent review and high-risk work. Include a no-separate-agent option when permitted; fresh context does not itself prove review quality. Do not infer planning or review ability from coding benchmarks alone.

Explore feasible model-effort pairs broadly before selecting portfolios, including stronger models at low effort versus lighter models at higher effort where relevant. Compare task success evidence, frequency, context, latency, usage, repair and escalation risk against quality requirements. Higher effort is not always better, nor lower effort always cheaper per successful task.

Start with the least costly plausible candidate per role. Estimate whole-workflow usage for representative scenarios, including activation frequency, context, retries, review and escalation. Separate measured results from estimates; use qualitative comparisons when numerical evidence is insufficient. Group pairs into relative cost tiers only when useful and supported; label API or benchmark tiers as proxies, leave unknown costs unknown, and do not force a complete ranking.

Where choices permit, construct distinct budget-first, balanced and quality-first portfolios, including selective activation and escalation. Compare credible alternatives for consequential roles and explain supported tradeoffs and unresolved comparisons. Preserve the user's preferred configuration as a candidate. Prefer the least costly configuration evidenced to meet quality thresholds; if evidence is insufficient, label the choice provisional. For a user prioritizing limited subscription allowance, default to budget-first unless they choose otherwise or evidence shows it fails quality. Recommend costlier defaults only with role-specific evidence; without a preferred candidate or sufficient evidence, propose a practical budget-first starting point without claiming an optimum. Specify escalation and fallback triggers and respect required independent review.

## Validation and output

When useful, propose a bounded comparison with identical inputs, acceptance and relevant context. Measure success, missed issues, repairs, elapsed time and usage per successful task, including follow-up. Account for coarse or shared meters, resets, background activity and small samples. Do not run costly evaluations without authorization or imply proposed runs occurred.

Provide a table per role with model, effort, rationale, cost or usage evidence, confidence and escalation. Show feasible portfolios and tradeoffs; explain changes to existing choices. Cite direct sources with checked dates, separate measurements from inference, and state unknowns and how to test them. End with a recommendation and editable policy delta, not an applied change.

Do not change account settings or repository/global model policy without explicit request. Confirm target-runtime availability; if current research or runtime views are unavailable, disclose the limitation and date the available evidence rather than presenting it as live.
