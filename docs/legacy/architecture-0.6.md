# Framework architecture and contribution guide

CDF separates specialist work from coordination. A skill describes how to perform one kind of work and the evidence specific to it. Its `SKILL.md` contains a name, an activation description and the method; optional references provide detail only when useful. A role describes a responsibility, its permissions and the skills and resources that work together. A role can be performed by the master or a delegated agent, subject to runtime restrictions.

`roles.json` is the source registry for role-to-skill and conditional-resource assignments. The installer generates runtime role instructions from it. `subskills.json` describes available integrations, helpers and specialist candidates; their presence there does not activate them for every role. `model-policy.toml` maps role policy keys to model and reasoning effort. The runtime determines which models and tools actually exist. Disk configuration cannot change an agent that is already running.

The delivery skill owns coordination and framework-wide completion gates. The decision-interview skill owns readiness and unresolved decisions. The implementation and specialist skills own their work methods; review and verification skills own their respective evidence methods. The installer owns managed files and recovery. User instructions and runtime rules take precedence over framework guidance.

The managed entrypoint repeats the review threshold so it remains visible before delivery loads. Role defaults repeat authorization and escalation boundaries because a delegated agent may not inherit the master's context. Delivery remains the detailed owner of coordination and review policy; update those entrypoint safeguards together when the policy changes. When a runtime restriction prevents required review or delegation, identify the restriction and report the blocked gate; never treat a self-review as independent.

## Master and delegated work

The master inspects the request and evidence, determines the outcome and material decisions, and selects direct work or a bounded role assignment. Investigate discoverable facts first. If a material decision remains open, ask when permitted and keep dependent implementation pending; continue independent work. Do not ask again about settled or routine details.

For delegation, pass the objective, observable acceptance, owned files or responsibility, baseline, constraints, settled decisions, open dependencies and expected evidence. Include applicable role and skill instructions and resolve its model-policy key against runtime availability. Only launch when the runtime permits it. The master integrates results, inspects evidence, resolves returned questions, and arranges required independent review. The role does not require a separate agent: small or dependent work can remain with the master.

A delegated agent reads its assignment, required role skills and applicable conditional resources. It investigates gaps, returns unresolved material decisions to the master before dependent edits, preserves other work, and reports changes, checks, findings and limitations. It does not create subagents. Runtime restrictions may impose additional limits.

## Adding a skill or changing a role

1. Define a specific outcome and boundary. Check existing skills for overlap and decide whether a focused change or reference is sufficient.
2. Create `skills/<name>/SKILL.md` with concise `name` and `description` frontmatter, activation conditions and a method that adds domain-specific value. Put substantial optional details in a local reference only when they materially help. Avoid copying global coordination rules.
3. Compose the skill in `roles.json` as required or conditional, with a specific activation for conditional skills. Update an existing role or introduce one only when its responsibility is distinct; map its policy key in `model-policy.toml`.
4. Add positive and negative activation scenarios and evidence for the resulting work. Run static guidance and packaging checks, then model task evaluations when available. A passing text check does not show that an agent selected or followed a skill.
5. Record research sources, inspected revisions, licensing and any reused content in `sources.json` and `THIRD_PARTY_NOTICES`; do not copy complete third-party skills. Preserve applicable licenses and attribution.

Use `python3 -m unittest discover -s tests` for the repository checks. See [evaluation cases](https://github.com/churakovra/code-delivery-framework/blob/3ff534627e8b10de3dba2c6443855e870567ef84/evaluation-cases/README.md) for task evaluation protocol and [README](https://github.com/churakovra/code-delivery-framework/blob/3ff534627e8b10de3dba2c6443855e870567ef84/README.md) for installation, model policy and recovery.
