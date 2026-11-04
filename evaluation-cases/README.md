# Delivery behavior evaluations

These prompts and rubrics are test inputs, not claims of success. `simple-counter-change` is an executable control. The remaining cases are scenario specifications: supply the runnable project, scripted user answers, and runtime conditions described in each case before scoring implementation. Keep setup identical across compared conditions; never show the rubric to the agent.

Run each case with the same model, harness, tools, and initial project state under the current framework and a baseline without it. Aim for three runs per condition and randomize order where practical. Capture unedited traces and check output. Score each criterion pass, fail, or not observed with evidence. Record actual delegation permissions, agent slots, and role settings; unavailable tools or agents are not evidence of a pass.

Record revision, model and harness, setup, prompt, run order, wall-clock duration, agent and tool calls, rework, and token or cost data when exposed. Mark unavailable measurements as unavailable. Compare quality and efficiency across runs and report variation and limitations. Do not claim improvement from the existence of these cases or from unexecuted model runs. The repository's local opt-in evaluation protocol may supply additional historical cases and result templates.

The explanation cases cover a code flow, guided practice across scripted turns, and a short-answer control. For the guided-practice case, record the learner attempt and follow-up implementation request identically across conditions. These are prompts and rubrics; no model results are implied.

The feature Git workflow case requires an isolated Git repository and the recorded variants described in the fixture. It is a scenario specification, not a recorded model run.

The cleanup Codebase Memory case includes a runnable fixture and specifies available and unavailable MCP variants and a coverage gap. Copy its ignored files too and confirm exclusion before scoring. It is not a recorded model run.

The implementation-readiness and modular-role-composition cases specify direct and delegated decision handling, standalone and composed skills, structural-discovery fallback, and independent-review variants. They are scenario specifications, not recorded model runs.

The routing-efficiency case compares bounded backend work, repository understanding, graph-evidence handoffs, and unrelated catalog skills. It requires the stated fixtures and runtime variants; it is not an executed model evaluation.

## Executable counter control

`python3 scripts/run_evaluation.py --runner /absolute/path/to/adapter --output /path/to/new/results --seed 0` runs the counter fixture once each with and without the current framework payload in separate temporary projects. The adapter is an executable which receives the prompt on stdin, runs with the project as its working directory, writes its trace to stdout/stderr, and exits zero only when its agent task completes. It is responsible for isolating the agent runtime, credentials, configuration, models and permissions; the harness does not provision or verify those. Use a trusted, deliberately configured adapter; the agent and subsequent check execute code on the local machine.

The output directory must not exist. It contains unedited stdout/stderr, workspace snapshots, run order and duration, and a focused counter behavior check after successful adapter completion. Runner errors, nonzero exits and timeouts are failures, not passes. The check does not score instruction following, code quality, skill discovery, or agent identity. Record the exact framework revision (including dirty state), adapter and model, permissions, and runtime separately. Repeat runs with varied seeds and inspect traces; one successful run cannot establish an improvement. No model task runs occur as part of the unit tests for this harness.
