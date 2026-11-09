---
name: cdf-documentation
description: Create or update only documentation that users, maintainers or operators need to understand a delivered contract, setup, decision or procedure. Use for documentation requests or behavior changes that stale existing docs.
---
# Minimal, accurate documentation

1. Identify readers and their task. Confirm whether existing docs already own this topic. Prefer updating the canonical document to adding another one.
2. Read verified behavior and authoritative tests/configuration. Distinguish implemented behavior from planned behavior; never fabricate completed features or checks.
3. Record only durable information that code alone cannot make easy to discover: public behavior, operational setup, breaking changes, invariants, migration/runbook steps and significant design tradeoffs.
4. Keep prose scannable and example-driven where useful. Avoid documenting trivial private functions, repeating every diff or generating a lengthy narrative for a small patch.
5. Check commands, links, examples and paths against current repository; avoid external-network checks unless permitted.
6. Report changed documentation and explicitly flag unknown behavior rather than guessing.

Choose how-to, reference, explanation or tutorial for the reader’s actual task without reorganizing unrelated documentation. For consequential setup/upgrade/runbooks include prerequisites, commands, expected state and recovery. Run a fresh-reader check: can someone without hidden chat context reproduce it on a disposable target? Mark commands that were not executed.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `anthropic-doc-coauthoring`: substantial RFC, design document or externally read technical spec; avoid full process for a README correction.
- `vercel-writing-guidelines`: requested editorial consistency audit; may fetch external rules and requires permission.
Fallback: canonical, evidence-backed documentation above.
