---
name: cdf-model-calibration
description: Evaluate and propose role- and task-specific Codex model/effort policies under subscription usage constraints. Use only for explicit calibration or model-policy review, never in routine coding tasks or during ordinary installation.
---
# Model and effort calibration (optional operator skill)

1. Identify actual Codex runtime, plan, selectable models and efforts, allowed delegation and current policy. Distinguish model *available* from model/effort *confirmed active*.
2. Collect versioned official product documentation, current usage-window rules and any meaningful independent evaluations. API prices are not ChatGPT Plus usage units; never convert them directly into remaining subscription allowance.
3. Define representative tasks by complexity/risk and compare total **usage per successful task** including clarification, context, retries, review, verification and repairs. Hold prompt, repo, tools and environment constant across candidates; record variations.
4. Propose budget, balanced and quality configurations with uncertainty. Use task complexity to decide when to escalate; fixed role mappings are only defaults.
5. Do not claim quantitative savings from word counts, unrelated benchmarks or unrun tests. Mark unknown measurement access explicitly.
6. Write a proposed policy delta and evaluation protocol; do not edit Codex/global config without explicit approval. Existing master model cannot be changed merely by editing a file in its current session.

Record available, requested and observed-active model/effort separately. Compare resources per accepted outcome, including retries, checks, review and worker overhead; an available candidate or proposed policy is not an active assignment. Routine development must not activate this skill or alter model configuration.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `openai-docs`: official model, Codex and usage documentation lookup when installed (avoid deprecated upstream packages; prefer current first-party capability).
Fallback: direct current official documentation and explicit unknowns. No LLM research during normal installation.
