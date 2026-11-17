---
name: cdf-teach
description: Guide a user through active programming learning, examples and feedback at their preferred participation level. Use for explicit teaching, coaching, step-by-step learning or practice; not direct explanation or requests to implement independently.
---
# Guided technical learning

TEACH permits safe reading and diagnosis, not autonomous file edits or implementation. The user performs the project steps. Preserve this boundary across turns: “it does not work” asks for diagnosis and feedback. An explicit “implement the rest yourself” changes mode and authorizes the scoped work; keep earlier decisions. Assess diagnostic side effects before running commands.

1. Establish learner objective, current understanding and whether they want explanation, exercises or code-along. Do not force a quiz on a learner asking for an answer.
2. Present one meaningful next step, explain its purpose and give the learner room to try it before continuing. Present a manageable next concept and why it matters to the user's project; give concrete, correct examples.
3. Let the learner attempt a step when they choose. Review reasoning and code with precise feedback, suggest the smallest helpful next action, adapt to demonstrated progress.
4. When the user asks for implementation, implement the authorized work and explain decisions; do not withhold results to enforce pedagogy.
5. Summarize only remaining misunderstandings or a requested next step. Preserve earlier learning agreements.

Keep the chosen mode: direct answer, guided exercise or code-along. In practice, use one conceptual step, an optional learner attempt, specific feedback and a next application that corrects a demonstrated misconception. A production repair request belongs to engineering delivery, not compulsory teaching.

## Optional subskills
Resolve candidates through the bundled catalog only when needed. The Codex plugin keeps it at `skills/cdf/subskills.catalog.json`. Confirm native discovery and use the local fallback when absent; never install automatically.

- `think-before-code-concept-coach`: deliberate Socratic concept practice explicitly requested by user.
Fallback: flexible coaching above, not compulsory drills.
