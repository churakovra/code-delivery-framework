# Regression Testing

Use when: A behavior change or repair with a meaningful observable regression.

Choose a check at the owning behavior boundary. Use the production path and an assertion that fails for the reported defect. Reproduce failure before repair when practical. Include relevant boundary or failure cases without duplicating implementation details. If a test is impractical, state why and use the strongest available check. Preserve project-required suites. Record the exact command and fresh result. Stop when the changed behavior and relevant regression are evidenced; do not impose a universal TDD cycle.
