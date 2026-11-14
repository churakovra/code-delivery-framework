# Compact solution proposal

For consequential choices state: outcome; observed paths/contracts and reuse; recommended minimal solution; why a simpler path fails if adding complexity; credible rejected options; scope boundaries; risk and earliest falsifying check; unresolved material question only if necessary.

Tie each nontrivial baseline addition to an observed requirement and a concrete reuse mismatch. Keep optional improvements conditional; a general best practice does not prove necessity. A few connected paragraphs suffice. This is a decision artifact, not private reasoning or a mandatory file. After the choice, an implementation plan may sequence dependencies and acceptance checks.

## Examples of the method

- Templates/CI: trace the existing publisher command, payload and environment configuration across ownership boundaries. Prefer invoking that command when its contract fits; add a bundle only for a demonstrated requirement. Preserve template bodies. Resolve material environment/publication choices before dependent CI edits; use a nonpublishing payload experiment first.
- Known private helper rename: inspect callers, rename and run a focused behavior check. No proposal, interview or architecture agent.
- Data migration: identify readers, writers, compatibility window, loss risk and recovery. Recommend a supported migration path; resolve destructive or compatibility choices before dependent changes. Test recovery on disposable data.
- Heavy tests complaint: identify what each expensive check protects. Recommend cheaper contract checks where they cover the risk; retain necessary integration/safety evidence. Do not blindly delete all tests or repeat an unchanged full suite.
