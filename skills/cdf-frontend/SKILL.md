---
name: cdf-frontend
description: Implement existing-product UI behavior, client state and frontend components with real accessibility and interaction checks. Use for interface code changes; visual redesign requires cdf-ui-design only when requested or consequential.
---
# Frontend engineering

1. Read the actual route/component, data contract, design tokens, state ownership, component library and tests. Reuse production components; do not recreate an existing component as a parallel implementation.
2. Establish expected UI behavior and supported states: loading, empty, error, success, disabled, retry, responsive and keyboard/focus paths where applicable. If product behavior is materially ambiguous, invoke `cdf-requirements` before dependent edits.
3. Keep data-fetch lifetimes, cancellation, server/client boundaries and error states consistent with installed framework versions. Avoid redundant state/effects and prevent fetch waterfalls where genuinely independent requests can be parallelized.
4. Prefer semantic HTML and proven accessible components. Check focus visibility, labels, keyboard navigation and errors on changed interactions; do not use ARIA to replace native semantics.
5. Maintain clear component APIs and ownership. Avoid abstraction by default; component composition helps only when it reduces actual duplication or boolean-flag proliferation.
6. Run relevant test/type/lint/build checks. For visually consequential work, inspect the rendered interface and interaction where tools permit. For persistent source/runtime disagreement, inspect the active route, version and configuration before more tuning. Technical checks do not establish perceived usability or game feel. Report browser or visual verification gaps without asserting they passed.

Trace the changed flow from action → handler → state → request/data → rendered feedback → error/retry. Check stale async results and double-submit where they affect that flow. Use the existing harness and components; do not add a browser framework or UI kit merely for a checklist. Static text does not need every interactive state.

## References
- `references/accessibility-and-states.md` only for interactive or accessibility-sensitive UI.

## Optional subskills
Resolve a candidate ID only when needed through `.codex/cdf/subskills.catalog.json` in the installation target or configured home. Confirm native discovery and use the local fallback when absent; never install automatically.

- `vercel-react`: React/Next.js performance, fetching or rendering tradeoffs.
- `vercel-composition`: reusable React component API or boolean-prop complexity.
- `vercel-web-guidelines`: explicit UI/UX/accessibility audit, with reviewed source and network permissions.
Fallback: framework docs, real components and focused checks; no React specialist for non-React projects.

Frontend owns interactions, state/data lifetimes, requests and accessibility. A visual specialist supports requested art direction; loading it does not verify functionality. Exercise the actual production route and inspect host capabilities before inferring behavior from generated assets. For source-backed diagrams, verify transitions against source separately from navigation and visual hierarchy.
