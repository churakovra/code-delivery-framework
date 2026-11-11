# Acceptance status

**MECHANICS_VALIDATED; BEHAVIOR_NOT_VERIFIED.** The current package version comes from `[project].version` in `pyproject.toml`. The source installs one discoverable CDF skill with nine core specialist modules, up to three optional modules, and two native agent templates. The separate source skills remain unchanged in organization. `cdf` owns delivery selection and coordination; the nine specialist core skills own their methods.

## Supported lifecycle

The installer supports fresh project/global installation, preview, status, upgrade, interrupted-operation recovery and uninstall. It recognizes the 10-core 1.2.x and recorded 12-core 1.1.0 flat inventories for migration and removal. A single-layout manifest records `layout: single` and requires every selected module guide and the module index. Older installers cannot read that new field; recovery and removal need the current installer. Upgrade removes owned retired skill files and installs the kernel, preserves selected extras and user text, and refuses modified-file conflicts and version downgrades.

Migration tests cover pinned 1.1.0 installations created by the original installer from repository revision `cf87b9fac0c94caa27cb2f5f45b1da2b11785f00`, plus adversarial synthetic fixtures. Both project and global targets are temporary. The current source upgrades those actual 1.1.0 payloads without a version override. Synthetic forward-version tests also cover ordering and rollback boundaries.

Frozen compatibility fixtures and evaluation baselines are inactive test data. They are retained to protect existing installations and honest historical comparisons; they are not installed into the current bundle. Retired skills, completed implementation plans and exploratory hooks notes are absent from the supported source. Source attribution remains in `sources.json` and `THIRD_PARTY_NOTICES`.

## Verification

Authoritative local checks are `python3 scripts/validate_cdf.py`, `python3 scripts/cdf.py validate --offline --json`, `python3 -m unittest discover -s tests` and `git diff --check`. Tests exercise dry-run bytes/modes/mtimes, conflicts, every upgrade replacement, legacy journals, committed recovery, partial uninstall, downgrade ordering and evaluation evidence integrity. On 2026-11-09, all 220 tests, both validators and diff checks passed. Independent review found no actionable source issues and verified the pinned baseline and fixture bytes against their recorded Git revision. Independent review is separate from author self-check.

No CI workflows, automatic third-party installation or hooks are bundled. Private-state ignore rules remain after uninstall; already tracked sensitive files need separate remediation. Installer mutations require POSIX. File status and configured templates do not establish live skill discovery.

## Evidence limits

No live model evaluations, independent live trace grading, held-out evaluation set, measured behavioral improvement or subscription savings are claimed. On 2026-11-10, a real app-server `skills/list` probe using the bundled Codex 0.167.0-alpha.3.2 in an isolated temporary home observed one enabled CDF entry, resolved small-SVG/large-PNG paths, and no discovery errors. That does not establish model routing or desktop rendering. Fake adapters and deterministic checks establish mechanics only. The pinned repository snapshots establish source identity, not a separately signed release artifact. Hashes detect inconsistency, not authenticity. The evaluation protocol distinguishes historical `CDF_20`, pinned `LEGACY_CDF_11` and current `CANDIDATE_CDF` guidance.

Live comparisons need an agreed model-run budget, a trusted adapter and appropriate external isolation. Temporary homes are not an OS sandbox. External dialogue/control declarations and runtime-policy attestations require review of actual traces. See the [evaluation protocol](../evals/README.md) for prerequisites and limits. No user credentials are copied into fixtures, and development does not upgrade live global configuration. Merging, publication and deployment are separate actions.

On 2026-11-10, all 230 tests, both offline validators, and diff checks passed for the single-entry change. Independent review found no remaining actionable findings after corrections to interrupted-recovery evidence and contradictory candidate activation expectations. The single-entry layout and skills-only plugin builder are checked through temporary install/upgrade/recovery/removal and payload tests. No live model runs establish specialist routing quality yet. Desktop cards and host plugin installation remain unverified. Colored PNG card assets and transparent small SVGs follow the inspected bundled OpenAI skill structure.
