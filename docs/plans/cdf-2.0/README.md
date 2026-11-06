# Code Delivery Framework 2.0 — Architecture Implementation Blueprint

**Status:** design specification, not deployed or runtime-evaluated.  
**Date:** 2026-11-05. **Baseline:** CDF v0.6.0, `3ff534627e8b10de3dba2c6443855e870567ef84`.  
**Companion:** `CDF_2_0_SKILL_SPEC.md` and `CDF_2_0_Skill_Pack.zip` prepared earlier in this conversation. Do not recreate or rename the 15 proposed CDF skills here.

## Purpose

An implementation-ready specification for the parts of CDF **outside the skill layer**: roles, Codex agents, task lifecycle, delegation, model routing, installer, safe upgrades, security, instrumentation, evaluation and migration. The documents contain the chosen defaults, edge cases, observable acceptance contracts and decisions about what CDF intentionally will **not** implement.

## Reading order

1. [Architectural decisions](docs/00-decisions-and-system-boundaries.md)
2. [Roles and runtime adapters](docs/01-roles-and-agent-profiles.md)
3. [Task state machine and requirements gate](docs/02-execution-state-machine.md)
4. [Delegation and handoff](docs/03-orchestration-and-handoff.md)
5. [Model and effort policy](docs/04-model-routing-and-usage.md)
6. [Installer, manifest and recovery](docs/05-installer-and-distribution.md)
7. [Evaluations and telemetry](docs/06-evaluations-and-observability.md)
8. [Migration and execution plan](docs/07-migration-and-implementation.md)
9. [Security, compatibility and operating procedures](docs/08-security-compatibility-operations.md)
10. [Concrete installer interfaces and error contracts](docs/09-implementation-interfaces.md)
11. [Skill–role runtime integration](docs/10-skill-role-routing-integration.md)

To hand a single PR implementation task to Codex, start with [IMPLEMENTATION_HANDOFF.md](IMPLEMENTATION_HANDOFF.md).

Contract examples: `templates/`, `policies/`, `schemas/`, `evals/`, and `tests/`.

## Priority and terminology

- `Primary skill`: self-contained `cdf-*` instructions from companion Skill Pack.
- `Subskill`: optional community instruction set; selected by primary skill when its documented trigger applies. **Not** a Codex subagent.
- `Subagent`: independent Codex context/thread, optionally with a custom agent role.
- `Role`: logical responsibility and competency profile, which the master can perform itself.
- `Runtime adapter`: capability-specific binding to the currently installed Codex CLI/app server; do not invent unsupported controls.
- `Gate`: a rule whose pass/fail is established by task evidence or a deterministic local tool; instructions alone provide advisory enforcement.

## Binding decisions

The plan is opinionated: one master session by default, high-risk review with independent evidence, no external dependencies in the core install, no automatic model research during install, no implicit credential access, no commit/push/deploy without authorization, and no end-user files overwritten on conflicts. Where a native Codex behavior may differ across versions, the adapter must detect it and degrade gracefully; it must not emulate permissions by claiming a role prompt creates isolation.

## What this deliverable does not claim

No CDF repository changes were applied. No real Codex-agent runs, subscription consumption measurements, installer transaction rehearsals or end-to-end evals were executed. The supplied schemas, TOML files and scenario definitions are reference implementation contracts, not currently activated CDF runtime files.
