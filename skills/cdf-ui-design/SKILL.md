---
name: cdf-ui-design
description: Design or substantially redesign a user interface based on audience, task, product identity and explicit brief. Use for new visual direction or meaningful interaction design, not routine frontend bug fixes.
---
# Visual brief, direction and acceptance

1. Inspect the product, audience, visual identity, existing design system and user task. Separate user-specified constraints from design decisions left open.
2. Clarify consequential questions: information hierarchy, required interaction, responsive priority, accessibility constraints and brand direction. Reuse the design system unless redesign is authorized.
3. For new visual direction or substantial redesign, prefer an available, compatible installed visual specialist such as the catalog’s `anthropic-frontend-design` candidate. Confirm native name/path, source revision, license and tool compatibility; read the actual skill before claiming use. Keep runtime/user/project authority above third-party methods. If absent or incompatible, continue with native design and this local fallback. Select intentional hierarchy, typography, spacing, imagery, semantic colors and interactive behavior. Avoid unrequested decorative novelty or a stock dashboard look.
4. Define representative flows and meaningful states: empty, loading, errors, validation, success, mobile and keyboard behavior. Explain only the decisions that affect implementation.
5. Specify an actionable design handoff (components, tokens, responsive behavior and acceptance). When code implementation is authorized, use `cdf-frontend`; do not build an unsolicited prototype.
6. When implementation is authorized, implement and inspect one representative end-to-end journey before repeating the design across screens. For design-only work, specify that journey and its acceptance without creating an unsolicited prototype. Inspect screenshots at relevant desktop/mobile widths and test navigation plus a failure state. Critique the focal task, hierarchy, typography, density, contrast, relationship readability and contextual explanations. Record remaining acceptance needs; screenshot existence alone does not establish visual acceptance.

Make the handoff testable: name component/token reuse, key actions, responsive behavior and keyboard/error states. Separate an accepted visual direction from optional proposals; a routine behavior fix does not authorize redesign. Rendered acceptance and remaining human judgment must be reported separately.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `anthropic-frontend-design`: distinctive visual direction for greenfield or major redesigns.
- `vercel-web-guidelines`: targeted existing UI accessibility/UX audit.
Fallback: product-derived decisions and concrete UI states above; never auto-install or override existing branding.

For process explorers, establish source-backed topology before styling; a visual specialist cannot establish domain semantics. Keep semantic, functional and visual verdicts separate. Seek user direction for material unresolved aesthetic choices, not each CSS value. Reuse a template only after the representative experience has been accepted.
