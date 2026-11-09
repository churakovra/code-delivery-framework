---
name: cdf-ui-design
description: Design or substantially redesign a user interface based on audience, task, product identity and explicit brief. Use for new visual direction or meaningful interaction design, not routine frontend bug fixes.
---
# Interface and interaction design

1. Inspect the product, audience, visual identity, existing design system and user task. Separate user-specified constraints from design decisions left open.
2. Clarify consequential questions: information hierarchy, required interaction, responsive priority, accessibility constraints and brand direction. Reuse the design system unless redesign is authorized.
3. Select intentional hierarchy, typography, spacing, imagery, semantic colors and interactive behavior. Avoid unrequested decorative novelty or a stock dashboard look.
4. Define representative flows and meaningful states: empty, loading, errors, validation, success, mobile and keyboard behavior. Explain only the decisions that affect implementation.
5. Specify an actionable design handoff (components, tokens, responsive behavior and acceptance). When code implementation is authorized, use `cdf-frontend`; do not build an unsolicited prototype.
6. Verify the resulting UI through rendered inspection when tools allow it; record remaining acceptance needs.

Make the handoff testable: name component/token reuse, key actions, responsive behavior and keyboard/error states. Separate an accepted visual direction from optional proposals; a routine behavior fix does not authorize redesign. Rendered acceptance and remaining human judgment must be reported separately.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `anthropic-frontend-design`: distinctive visual direction for greenfield or major redesigns.
- `vercel-web-guidelines`: targeted existing UI accessibility/UX audit.
Fallback: product-derived decisions and concrete UI states above; never auto-install or override existing branding.
