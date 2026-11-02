# Delivery behavior evaluations

These prompts and rubrics are test inputs, not claims of success. `simple-counter-change` is an executable control. The two other cases are scenario specifications: supply the runnable project, scripted user answers, and runtime conditions described in each case before scoring implementation. Keep setup identical across compared conditions; never show the rubric to the agent.

Run each case with the same model, harness, tools, and initial project state under the current framework and a baseline without it. Aim for three runs per condition and randomize order where practical. Capture unedited traces and check output. Score each criterion pass, fail, or not observed with evidence. Record actual delegation permissions, agent slots, and role settings; unavailable tools or agents are not evidence of a pass.

Record revision, model and harness, setup, prompt, run order, wall-clock duration, agent and tool calls, rework, and token or cost data when exposed. Mark unavailable measurements as unavailable. Compare quality and efficiency across runs and report variation and limitations. Do not claim improvement from the existence of these cases or from unexecuted model runs. The repository's local opt-in evaluation protocol may supply additional historical cases and result templates.

The explanation cases cover a code flow, guided practice across scripted turns, and a short-answer control. For the guided-practice case, record the learner attempt and follow-up implementation request identically across conditions. These are prompts and rubrics; no model results are implied.

The feature Git workflow case requires an isolated Git repository and the recorded variants described in the fixture. It is a scenario specification, not a recorded model run.

The cleanup Codebase Memory case specifies available and unavailable MCP variants and a coverage gap; it requires a suitable repository fixture before execution. It is not a recorded model run.
