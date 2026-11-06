# Applying an operator-selected policy

Read only the policy path explicitly selected by the operator. The repository example `policies/model-routing.example.toml` is a proposal, not an automatically activated setting or installed user configuration. Do not search credentials or rewrite Codex configuration to find/apply it.

1. Select its `selected_profile` (`budget`, `balanced`, or `quality`). Read `parallel_agents_max`, `review_medium_by_default` and `allow_unverified_fallback`. Cap concurrent workers at that budget and two by default; a user-authorized override must be explicit. Count workers already active before launching another.
2. Independently assess risk. High risk always requires independent review; medium risk does when the profile requests it or shared contracts, weak failure evidence or uncertain rollback warrant it. A missing mandatory reviewer means BLOCKED_REVIEW.
3. Classify cognitive complexity t0–t3 separately from risk. Select the role/tier candidate. Check actual runtime model/effort pairs and per-spawn support before requesting it. No catalog is not proof of availability.
4. An explicit user model requirement forbids substitution. For a preference, use a disclosed inherited fallback only when allowed. Record candidate, request, observed pair and any fallback separately. Never switch the current root model through a policy file.
   Supported `[fallback]` rules are `inherit_with_disclosure` or `block` for unavailable models, `runtime_default_with_disclosure` or `block` for unavailable efforts, and `block_required_review_and_offer_human_review` for missing reviewers. Unsupported values must be rejected. Missing mandatory review blocks final readiness; approved implementation and verification may still proceed before the patch is ready.
5. In a source checkout, `python3 scripts/inspect_cdf_policy.py --policy PATH --risk HIGH` provides a deterministic advisory report using the same rules. It does not probe models or launch agents. An installed skill can apply these short rules directly; it does not require Python or a wrapper engine.

No policy supplied: use the existing session settings, direct-first execution, risk-based review and a maximum of two concurrent workers. Policy examples and instruction word counts establish no subscription savings.
