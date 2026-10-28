---
name: model-routing
description: Compare available models and reasoning efforts across agent roles to find useful quality at the lowest practical usage or cost. Use when choosing or reviewing a role-to-model configuration.
---

## Scope and profile

Recommend configurations for the user's actual roles, runtime, plan, workload, and quality requirements. Read [selection-profile.toml](references/selection-profile.toml) when present. Preserve user choices and constraints. Treat earlier recommendations as hypotheses, not facts or binding defaults. If the profile is absent, label assumptions and ask only for missing information that could change the recommendation.

Optimize for the lowest practical cost per successful task, subject to the user's quality and risk requirements. Include failed attempts, review, repairs, escalation, latency, and repeated context in that cost. Do not assume that the cheapest call or the strongest model is the best value. Do not store dated model rankings, prices, or claims in the profile.

## Research

1. Identify the exact runtime, plan, available models and supported efforts, usage windows, and active limits. Prefer the runtime's own model and usage views. Distinguish a listed model from one confirmed selectable for each role. Account for role instructions and any fixed model assignments.
2. Research current official provider model, product, and plan documentation, plus independent benchmarks where available. Search for role-relevant evidence and cost or token observations, not just broad model rankings. Check dates, benchmark methods, task match, model versions, and reasoning settings. Follow relevant sources from user material to their origin. Exclude models unavailable in the target runtime.
3. Separate verified facts, benchmark observations, proxies, and inference. State when evidence does not compare the specific model-effort combinations or workload. API prices and benchmark tokens do not directly measure subscription allowance. A remaining account percentage alone does not establish per-task usage. Do not invent savings, rankings, or task counts.

## Compare configurations

For each role, identify its actual work, frequency, stakes, activation conditions, context needs, and observable success criteria. Distinguish planning from implementation, QA from independent review, and ordinary work from high-risk work. Do not assign a separate agent to every task by default. Include a no-separate-agent option where the workflow permits it, and account for repeated context when agents are used.

Explore a broad set of feasible model and effort combinations before selecting a few portfolios. Compare different models at different efforts, including stronger models at low effort against lighter models at higher effort when relevant. Evaluate role fit, evidence of task success, expected frequency, latency, total usage, repair and escalation risk, and quality requirements. Fresh context may improve independence, but does not prove review quality. Do not infer planning or review capability from coding benchmarks alone. Do not assume a higher effort is always better or lower effort is always cheaper per successful task.

Construct meaningfully distinct budget-first, balanced, and quality-first portfolios when the available choices permit. Consider selective activation and escalation, not only fixed assignments. Compare the most credible alternatives for each consequential role and explain why they win, lose, or remain unresolved. Eliminate a choice only when evidence supports the tradeoff. If quality or consumption is unknown, present the choice as provisional instead of claiming it is cheapest or best. Preserve the user's preferred configuration as a candidate and explain evidence for any proposed change.

Prefer the least costly configuration that has evidence of meeting the role's quality threshold. Where evidence is insufficient, recommend a practical starting configuration and a comparison rather than asserting an optimum. Specify triggers for escalation and fallback. Respect required independent review and other workflow constraints.

## Validation and output

When useful, propose a bounded comparison on representative tasks with the same inputs, acceptance criteria, and relevant context. Measure task success, missed issues, repairs, elapsed time, and usage per successful task, including follow-up work. Account for shared or coarse usage meters, resets, background activity, and small samples. Do not run costly model evaluations without authorization, and never imply a proposed evaluation was executed.

Present a concise table for each role with the recommended model and effort, role-specific rationale, cost or usage evidence, confidence, and escalation. Show the alternative portfolios and the key tradeoffs, including unresolved comparisons. Cite direct sources with checked dates and distinguish measured facts from inference. State material unknowns and how to test them. End with a recommended configuration and an editable policy delta, without treating the delta as an applied change.

Do not change account settings or write a repository or global model policy unless the user explicitly asks. Confirm availability in the target runtime. If current research or runtime views are unavailable, disclose that limitation and use only dated, available evidence. Do not describe stale data as a live catalog.
