# 10 — Exact skill/role/runtime activation matrix and conflict resolution

This document is the integration contract between the companion CDF Skill Pack and the architecture, and takes precedence over any implied role-to-skill lists in legacy v0.6 `roles.json`.

## 10.1 Essential distinction

Three different routing mechanisms must not be conflated:

1. **Codex native discovery:** advertises installed skill names/descriptions; selecting a skill loads its `SKILL.md`. It is not a deterministic dependency resolver for CDF's JSON registry.
2. **CDF role instructions:** a *behavioral* instruction to use a relevant primary CDF skill for an actual assignment. The root may apply the same role without any child.
3. **CDF subskill catalog:** advisory metadata for optional community skills. A primary skill may request candidate ID only when concrete activation triggers hold; external skill must already be installed and safe. This is not automatic `import` or remote installation.

No secondary Python orchestrator is required to force-load a skill by reading every skill file. Correct runtime selection is measured with positive and negative evals.

## 10.2 Task → role → primary skills → optional community capability

| Task | Logical role (execution) | Primary skills selected | Optional community capability |
|---|---|---|---|
| Ambiguous product behavior | Root MASTER | `cdf-requirements` | grilling or brainstorming only for deep decision tree |
| Small well-specified backend change | Root ENGINEER | `cdf-implementation`, `cdf-backend`, `cdf-verification` | none by default |
| New API contract | Root/worker ENGINEER | `cdf-backend`, `cdf-implementation`, `cdf-verification` | API design candidate when design decision significant |
| PostgreSQL schema/concurrency | Root/worker ENGINEER | `cdf-backend`, `cdf-verification` | PostgreSQL/async subskill if specialized depth needed |
| React performance pathology | Root ENGINEER | `cdf-frontend`, `cdf-debugging` | Vercel React best practices if relevant |
| Substantial new visual interface | Root DESIGNER competency | `cdf-ui-design`, `cdf-frontend` | Anthropic frontend design (deep visual) |
| Unknown code flow | Root EXPLORER competency or native explorer | `cdf-codebase-research` | optional Codebase Memory integration if available and fresh |
| Failed implementation twice | Root/diagnostician | `cdf-debugging` | Superpowers systematic debugging if diagnosis complex |
| High-risk proposed diff | `cdf_reviewer` independent | `cdf-code-review`, relevant `cdf-verification` | differential security review only when applicable |
| Multi-phase approved feature | Root MASTER/ENGINEER | `cdf-orchestration`, `cdf-planning`, domain skills | writing/executing plans when task length warrants |
| Docs-only change | Root ENGINEER | `cdf-documentation` | document coauthoring only for complex docs requested |
| Teaching/explanation request | Root MASTER | `cdf-explain` or `cdf-teach` if optional pack installed | relevant external teaching skill if useful |
| Model and effort calibration | Explicit operator-only | `cdf-model-calibration` | official docs lookup; no runtime model change |

`cdf-orchestration` need not be loaded for casual explanation/typo tasks and its full method is not to be repeated in every profile TOML. Project `AGENTS` keeps the minimal guarantees always present.

## 10.3 Rule deduplication ownership

| Rule | Source of truth | Other layers refer only |
|---|---|---|
| User material decisions / READY-BLOCKED | `cdf-requirements` + minimal AGENTS guard | Roles, workflow docs |
| Direct-vs-delegate | `cdf-orchestration` | Native child profiles do not reimplement routing |
| Scope/permission boundaries | Runtime + user/project instructions | Role instructions and AGENTS reinforce, do not claim enforcement |
| Reuse, smallest patch | `cdf-implementation` | Domain skills add domain-specific rules |
| Backend invariants | `cdf-backend` | Reviewer uses only relevant reference |
| UI components/states | `cdf-frontend`, design choices in `cdf-ui-design` | No duplicate design helper |
| Verification evidence | `cdf-verification` | Code-review checks sufficiency, not duplicate suite |
| Independent review findings | `cdf-code-review` | Orchestration decides when needed |
| Runtime model settings | Codex runtime; advisory `cdf-model-calibration` | Role files do not pin models |
| Filesystem ownership | Installer manifest+journal | No LLM or skill may bypass collision checks |
| External candidate selection | `subskills.catalog.json` + owning primary skill | Not in AGENTS, not in generated role prompt en masse |

## 10.4 Conflict resolution procedure

When activated skills contain incompatible advice:

1. Follow current user/project/runtime authority first.
2. Use primary CDF skill for task workflow and task-specific invariant.
3. Apply optional subskill methods only to the extent they add a distinct necessary capability; do not import unrelated blanket rules.
4. Keep one method per step. For example, Superpowers TDD may inform a high-value regression test but cannot force TDD or reviewer-after-every-step across all CDF tasks.
5. If the conflict changes material behavior or user-visible contract, root asks the user; don't resolve it by choosing a louder skill.
6. Record a persistent conflict only when needed to update skill triggers, not a document for every task.

## 10.5 Activation examples for acceptance

**Positive:** “Migrate this PostgreSQL table while traffic continues” → `cdf-backend`, its persistence/contracts reference, `cdf-requirements` if rollout/compatibility unresolved, targeted Postgres community subskill if available; high-risk review.

**Negative:** “Fix a typo in README” → no backend, async, architecture, Postgres, review or planner subagent.

**Positive:** “Why is TaskGroup cancellation not cleaning up?” → `cdf-debugging`, backend async reference, deep systematic-debugging when cause is nontrivial.

**Negative:** “Rename local variable in known file” → no Codebase Memory indexing, no architecture reference, no new plan file.

**Positive:** “Review authorization diff” → reviewer loads `cdf-code-review`, optional differential security only with actual auth risk, independent finding evidence.

**Negative:** “Explain concurrency to me” → learning/explanation mode, no source modifications or mandatory task-review ceremony.

## 10.6 Packaging extras

Install these 12 by default: `cdf-backend`, `cdf-code-review`, `cdf-codebase-research`, `cdf-debugging`, `cdf-documentation`, `cdf-frontend`, `cdf-implementation`, `cdf-orchestration`, `cdf-planning`, `cdf-requirements`, `cdf-ui-design`, `cdf-verification`.

Extras: `operator` → `cdf-model-calibration`; `learning` → `cdf-explain` and `cdf-teach`. Add `agents/openai.yaml` metadata with `policy.allow_implicit_invocation: false` for operator-only calibration (supported runtimes only); it remains manually invocable. For learning extras, normal intent-based activation is acceptable; `cdf-teach` already requires an explicit user-guided-learning request. Do not globally disable `cdf-requirements` because it must be available for ambiguous feature work.

## 10.7 Acceptance

1. CDF_20 core default advertises exactly 12 primary skill names, and no `delivery` legacy name.
2. A role-assigned worker can use selected primary skill(s) without loading all 12 bodies.
3. Subskill ID never becomes a claimed installed skill merely because present in registry.
4. Model calibration never runs implicitly as part of ordinary code task or install.
5. No root AGENTS content duplicates the full requirement, verification or orchestration procedural text.
6. Positive/negative activation runs observe appropriate skill loads when runtime exposes them; otherwise report unobserved, not passed.
