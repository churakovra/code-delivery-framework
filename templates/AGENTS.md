# Delivery defaults

Before actionable repository work, read the delivery skill. Use its path from the available skills catalog when present. Otherwise, check `.agents/skills/code-delivery-framework/delivery/SKILL.md` in the repository and, if absent, `~/.agents/skills/code-delivery-framework/delivery/SKILL.md` for the default global installation. For a global installation with a custom home, use `<configured --home>/.agents/skills/code-delivery-framework/delivery/SKILL.md`. A global installation does not require a copy in each repository. Follow the delivery skill's routing and load only skills required by the assigned task; use exact skill paths named by any role-specific instructions. Only if the skill is unavailable at all applicable locations, follow this file without assuming other bundle skills exist.

For every user-facing response and agent handoff, read and apply the installed `asd-ste100` skill. Use the available skills catalog or the framework target's `.agents/skills/asd-ste100/SKILL.md`. Preserve required facts, uncertainty, and evidence. Higher-priority instructions and the user's requested format take precedence.

Preserve the user's scope and existing work. Do not stage, commit, open pull requests, merge, publish, release, deploy, or change branches without explicit authorization. Follow repository instructions and required checks.

For each task, capture the baseline, requirements, ownership, and observable acceptance criteria. Inspect the complete task diff and relevant callers or failure paths. Keep edits within assigned files and coordinate overlapping ownership.

Use one main agent loop for low or ordinary work. Ordinary implementation includes focused checks and self-review. Independent review is required for high-risk work such as authentication, permissions, money, persistent-data integrity, migrations, shared contracts, concurrency, or broad lifecycle changes; include relevant integration or compatibility evidence. QA may separately map acceptance criteria to checks when useful. Planning, design, and delegation are optional when complexity justifies them. Do not nest delegation: only the primary agent may assign agents, keeping the tree at two levels maximum. Give each agent a bounded ownership brief.

Review raw diffs, command output, and artifacts rather than accepting an agent's success claim. Do not weaken requirements, assertions, or fixtures to get a pass. After two unsuccessful repair cycles for the same acceptance failure, stop and obtain independent diagnosis before another fix.

Do not initiate exploratory browser walkthroughs or screenshot-based acceptance unless requested. Required automated browser suites still apply. The user performs manual UX acceptance.

Report changed files, checks actually run and results, limitations, blockers, and a short manual acceptance checklist. Mark missing required checks or reviewers as blocked; never imply unrun evaluations passed.
