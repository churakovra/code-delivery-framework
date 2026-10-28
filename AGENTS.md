# Framework development instructions

This repository develops a portable delivery-guidance bundle and its installer. Keep skills model-neutral and focused; skills should add useful task-specific guidance without repeating generic agent competence. Use progressive disclosure only where a reference materially reduces the entrypoint.

The bundled `templates/AGENTS.md` is consumer guidance inserted as a managed block. Preserve user-authored text and bytes outside that block. Existing instructions may conflict; expose and resolve migration conflicts rather than silently replacing user content.

Treat the framework installer and manifest as a recoverable lifecycle. Do not mutate the developer's live global configuration while developing or validating. Use temporary targets and dry runs. Keep docs aligned with the actual CLI contract and explicitly mark implementation or evaluation gaps.

Source research informs original concise adaptations. Do not copy complete third-party skills or rules. Record source URLs, exact inspected revisions, licenses, and any reused content in `sources.json` and `THIRD_PARTY_NOTICES`; retain required attribution and license texts for reused material.

Evaluation cases are prompts and rubrics, not claims of success. Do not fabricate model runs. Report which evaluations were actually executed and the limits of that evidence.

Write user-facing responses and agent handoffs in plain, concise language. State the outcome first. Use short sentences and active voice. Keep necessary facts, conditions, uncertainty, and evidence. Apply this guidance to the main agent and all roles.
