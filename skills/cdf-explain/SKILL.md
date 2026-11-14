---
name: cdf-explain
description: Explain code, system behavior or technical ideas clearly with grounded paths and a concise example. Optional learning pack; use for direct explanations, not unsolicited coaching or implementation.
---
# Explain code and systems (optional)

1. Answer the actual question first, at the requested depth. Define the relevant actors and data flow before detailed internals.
2. For repository-specific explanations, inspect real code/test paths; load `cdf-codebase-research` only if tracing across modules is required.
3. Show one concrete example or diagram only when it resolves confusion. Separate observations, deductions and assumptions; cite paths/symbols.
4. Avoid unsolicited redesigns, exercises and broad tutorials. If the user explicitly wants guided practice, use `cdf-teach` instead.

Distinguish what, how, why and execution-trace questions. For a trace, ground the input, owner and output in real paths and identify inferred edges or relevant failure cases. A request for explanation does not authorize edits or an unsolicited quiz.

## Optional subskills
Resolve candidates through the bundled catalog only when needed. The Codex plugin keeps it at `skills/cdf/subskills.catalog.json`. Confirm native discovery and use the local fallback when absent; never install automatically.

- `jjenksy-explain-code`: explicit visual/diagram-rich code explanation when available.
Fallback: grounded concise explanation above.
