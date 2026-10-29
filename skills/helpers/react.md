# React

Use when: React or Next.js code with relevant rendering, fetching, or performance concerns.

Follow the installed framework version and project conventions. Keep server/client boundaries deliberate and avoid moving unnecessary code into client bundles. Start independent data requests concurrently when their ownership and error handling permit it. Avoid request waterfalls, redundant effects, unstable list keys, and state derived unnecessarily from existing values. Preserve cleanup and cancellation behavior. Apply memoization or code splitting only for a concrete performance concern. Check production components with relevant type, interaction, and build checks. Stop when the affected behavior and identified concern are evidenced; do not perform unrelated optimization.
