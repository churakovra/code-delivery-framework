# Handoff to Codex: implement CDF 2.0 in controlled PRs

You are implementing an approved architectural migration, not designing a new one. Read `README.md`, `docs/00-decisions-and-system-boundaries.md`, `docs/07-migration-and-implementation.md` and **only the phase-relevant** deep specification. Read companion `CDF_2_0_SKILL_SPEC.md`/Skill Pack for actual primary skills; do not invent alternative names or replace them without demonstrated evaluation evidence.

**Baseline:** CDF v0.6.0 at `3ff534627e8b10de3dba2c6443855e870567ef84`. Confirm current working tree and HEAD; if they differ, inspect changes and preserve them. Do not modify user's installed global Codex config or ordinary app code during installer tests. Do not install third-party binaries or execute unreviewed community scripts.

**Work order:** PR-00 baseline/evals skeleton → PR-01 selected skills → PR-02 role TOMLs → PR-03 readiness/orchestration → PR-04 core installer → PR-05 safe lifecycle/legacy report → PR-06 model policy → PR-07 agent evaluations → PR-08 cleanup/release. Keep scope one PR at a time; each phase has explicit acceptance in `docs/07` and `tests/ACCEPTANCE-MATRIX.md`. Staged deployment and release require authorization.

**Core choices you must preserve:** one root agent by default; material user decisions before dependent edits; 12 core CDF skills, 1 operator and 2 learning optional; built-in worker/explorer; custom `cdf_reviewer`, `cdf_diagnostician` without pinned models; high-risk independent review or blocked status; no network/model call during core installation; user-owned files never overwritten; manifest+journal crash recovery; manual-only v0.6 migration for v2.0.0; optional Codebase Memory; no assumed Plus token conversion.

**Before coding:** check relevant existing implementation/tests and confirm the request includes a particular PR phase. Identify only **new material ambiguities** not settled by these documents; do not re-ask routine design decisions. If a source implementation differs, cite it and propose the least disruptive migration, not an unapproved redesign.

**After coding:** show changed paths, diff summary, exact commands and fresh outputs, failed/unavailable checks, review status and any remaining scope. Do not claim full CDF 2.0 success until real runtime tests and release gates pass. No staging/commit/push unless authorized.
