# Bounded subagent contract

A subagent is an execution method, not the definition of a role.

```yaml
role: engineer | explorer | reviewer | specialist
objective: <one measurable outcome>
scope: [<files or question>]
baseline: <commit/working-tree state>
confirmed_decisions: [<only consequential already-settled decisions>]
acceptance: [<observable checks>]
dependencies: [<what is ready or blocked>]
permissions: <read-only or explicit edit ownership>
return: [changed files, raw check pointers, concrete findings, limits]
```

The master must ensure compatible overlapping files and settled shared contracts before parallel implementation. Pass existing useful structural evidence rather than asking children to rediscover everything; stale evidence requires a fresh read. Prevent nested subagent trees unless a future evaluation proves benefit and runtime permits it.

**Delegation decision:** Is work independent? Does fresh context improve success? Can an owner safely integrate? Will review reduce a meaningful risk? If all answers are no, keep direct execution. The required independent review of a high-risk diff may be more valuable than a second implementer.

Do not claim model assignment worked from TOML alone; runtime capabilities are authoritative. If required independent review is unavailable, report this as an acceptance limitation.

For outcome investigations and reviews, include the original complaint, preserved behavior, failed hypotheses and evidence limitations in the objective/acceptance context. Ask whether the checks could detect that complaint. Do not present a narrow compatibility review as acceptance of the overall experience.
