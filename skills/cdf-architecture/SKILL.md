---
name: cdf-architecture
description: Recommend minimal architecture from observed contracts, reuse and tradeoffs before costly implementation. Use for migrations, structural choices and consequential technical uncertainty; not known local fixes, routine names or code-only diff review.
---
# Architecture before code

1. **Discover:** consume the accepted outcome and requirements evidence. Trace real entry points, callers, payloads, ownership, configuration and failure semantics. Research only gaps that affect the choice; do not repeat settled interviews.
2. **Options:** start with reuse or the smallest local change. Compare 1–2 credible alternatives when tradeoffs exist. A plan of implementation steps is not an architectural justification.
3. **Critique:** test each added abstraction against a proven contract/risk. Explain why reuse or a simpler path fails, maintenance and recovery costs, scope and operational assumptions. Include new formats, intermediate artifacts, validation rules and operational stages in this critique, not just services or classes. For each nontrivial addition cite the observed requirement and the existing mechanism’s concrete mismatch. General best practices or possible future needs are not that evidence. If necessity is unproven, remove it from the recommended baseline.
4. **Recommend:** present the chosen solution with source evidence, rejected alternatives, boundaries and remaining uncertainty. Share concise engineering rationale, not hidden reasoning. Keep the baseline supported by current requirements distinct from optional changes contingent on unresolved decisions. Do not recommend a dependent operational design while calling its requirements unknown. Use `references/solution-proposal.md` when useful.
5. **Early evidence:** select the smallest credible contract or end-to-end experiment that could falsify the consequential assumption. A dry run or fake transport may check a payload, but cannot establish real publication.
6. **Decide:** resolve material behavior, compatibility, data, permission and cost choices before dependent edits. Make routine choices directly. Continue already authorized implementation without asking again. Read-only research never authorizes implementation or publication.

Fallback: targeted source inspection and a short in-context recommendation; no architecture framework, mandatory document or extra agent. Use requirements for unresolved user decisions and domain skills for execution. Reading this guide is not proof that its method affected a decision.
