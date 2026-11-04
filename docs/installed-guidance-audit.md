# Installed guidance audit — 2026-11-04

Scope: local CDF and system skill entrypoints, global AGENTS/configuration routing, and high-overlap plugin entrypoints. Cached plugin files are not proof that their instructions are active. This is not an exhaustive semantic review of every plugin reference. No live global files were changed.

## Findings

- The global CDF installation under ~/.agents/skills/code-delivery-framework still contains pre-rewrite routing. Its delivery entrypoint omits general repository-understanding requests. Workspace changes do not update that installation.
- The Google Drive 0.1.22 router (skills/google-drive/SKILL.md:42) sends new Slides work to google-slides and describes an old mandatory PPTX workflow; google-slides/SKILL.md:10 routes new creation to Presentations instead. Update the plugin through its supported lifecycle rather than editing cached files.
- Installed Codebase Memory SKILL.md:8 claims roughly 500 versus 80,000 tokens without local measurements. Treat this as an upstream claim, not evidence of savings. Its description contains about 73 words of overlapping structural triggers.
- Large on-demand skill bodies include Excel live control (10,904 words), spreadsheets (9,683), documents (5,540), presentations (5,008), and the Data index (2,648). These are word counts, not measured tokens or always-loaded context.
- The Data index prescribes large full-read output budgets. Output caps do not themselves consume tokens, but full reads can increase context use; its reference map must remain conditional.
- Local ~/.agents/skills and ~/.codex/skills contained 20 SKILL.md files totaling 11,106 words, with no duplicate declared names. Plugin caches are outside this count.

## Codebase Memory evidence and repair

The live MCP successfully listed the CDF project, reported its index ready, returned payload/dependency_inventory symbols with no further result pages, and reported no recorded coverage issue for the checked framework, helper and registry paths. Coverage is best-effort, not proof of completeness. Source files were read to verify the routing.

The workspace helper now specifies bounded queries, reuse of current graph evidence, coverage/pagination checks, structured parent-to-child evidence, and honest source fallback when a child lacks MCP tools. It explicitly rejects treating tool-output-size claims as measured savings. Existing delivery and role activation routes cover repository exploration and understanding.

The 16 static guidance checks passed after the repair. These checks and the live MCP calls establish routing text and tool availability, not guaranteed compliance on every future task. Global installation activation and comparative token savings remain unverified.
