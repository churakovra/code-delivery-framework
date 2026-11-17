# Architecture and contribution guide

CDF supplies engineering guidance through one native plugin,
`code-delivery-framework`. Codex owns models, tools, permissions, approvals,
hook trust and the agent lifecycle. CDF adds no agent engine or enforcement layer.

## Skills and package

`skills/*/SKILL.md` is canonical method content. `cdf_registry.py` selects 14
standard skills and explicit optional model calibration. `cdf` owns interaction
intent, authority and delivery depth; specialists own their methods. Teaching,
explanation and meaningful testing are standard. The learning flag is a no-op
compatibility alias. Source skill bytes and references survive packaging.

`scripts/package_cdf_plugin.py` builds assets, standalone skills and hooks from
the existing templates; it does not install them. Root `plugin.json` uses the
official `extensions.com.openai.hooks` path. Its compatibility overlay points
to the same file and has the same identity. Native loaders select one source.
For known native clients that suppress hook discovery in the presence of a root
manifest, target-client detection emits compatibility-only layout. This is a
loader workaround within the same product, not a second desktop distribution.
Old profile flags remain aliases. Unknown-client discovery is not assumed.

## Native context and observation

`hooks/hooks.json` declares one handler per event. `hooks/cdf_context.py`
returns deterministic English additionalContext for SessionStart (including
startup/resume/clear/compact/fork), UserPromptSubmit and SubagentStart. The core
contract supplies intent/authority, minimal solution, skill loading, completion
and evidence rules. The turn reminder routes only relevant methods. The child
context preserves bounded authority; parents still supply concrete decisions.
The full methods remain in skills, which are not all loaded automatically.

The handler uses only Python standard library. It does not inspect prompts,
source or transcripts, classify intent with regex, call external services,
change Codex permissions, or run a loop. No PreToolUse or Stop gate is added.
After flushing context JSON to stdout, `hooks/observe.py` can append bounded
allowlisted event/session/time/hash history in host PLUGIN_DATA. Missing or full
history does not prevent context output. No prompt, model, source or tool data
is retained. Trust and sandbox remain native boundaries.

`cdf_runtime/hooks.py` reads plugin/list, skills/list and hooks/list, plus only
an explicitly selected bounded history file. Doctor separates installation,
discovery, trust, duplicates, execution history, context emission, receipt and
method application. Neither metadata nor stdout establishes intellectual use.
It never grants trust or modifies live configuration.

## Existing lifecycle and evaluation

Frozen 1.1, 1.2–1.5 and 2.0 ownership inventories and historical learning extras
remain available for recovery. `cdf_installer/agents.py` manages only explicitly
requested role setup, using existing recoverable transactions. Model policies
and configured TOMLs do not prove native role execution.

`evals/runner.py` uses the packager and native plugin manager in a fresh isolated
home for CANDIDATE_CDF. It verifies installed file bytes and archives packaged
guidance and installation receipts. It never replaces candidate setup with an
AGENTS block. External adapters require native Codex for installation and must
honor that home; their actual loading still needs evidence. Historical
snapshots/rubrics remain separate and unchanged. Native versus historical
materialization uses different loading surfaces, so comparison remains
descriptive; standardized parity cannot silently treat them as equivalent.

No new behavioral cases, runner service or model evaluations are added. Existing
historical tests calling retired CLI actions remain separate maintenance work.
Use only bounded technical checks for this change; manual model behavior and
comparative quality belong to the user. Preserve original notices and provenance
in `sources.json` and `THIRD_PARTY_NOTICES`. See [installation](installation.md)
for the single GitHub/native-manager workflow and trust review.
