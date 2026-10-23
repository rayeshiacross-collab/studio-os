# First Domino EP11 — Studio OS intake

The old `rebootv2-autopilot` CPU-render workflow has been retired. This is the replacement production lane in **Studio OS**, powered by **ComfyUI / Wan 2.2**, not the Supertonic+FLUX CPU pipeline.

- Episode: `FD_EP11`, “She Stayed Too Long Because Nothing Was ‘Bad Enough’”
- Spoken script: existing `rebootv2-autopilot/EP11_Narration_v1.txt` (leave original intact).
- Audio: owner already has EP11 audio. **Import exactly the owner-chosen recording**; do not generate Supertonic or substitute narration. The old `EP11_Female_Warm_Review_v2.mp3` is an existing candidate, not assumed to be the recording the owner chose.
- Visual lane: realistic **human** First Domino narrative; preserve Claire's character across shots. Do not use motion_batch's object-only runner for scenes with Claire.
- Render requirements: running compatible ComfyUI/Wan instance, tested API-format workflow and bindings, approved character reference and uploaded/mounted narration. Studio OS does not presently expose an API accepting audio in `/generate`.
- State: **intake/staged only**. This file is not a completed render, launched worker, or proof of a working server.
- Control: no publication, no paid API, owner watches/listens before approval; Hermes only receives approved final media.
- Run tracking: retain output checksums, playback review, audio hash, workflow/model identifiers, failures and owner-approval state alongside the Studio job. Don't infer successful runs from commits.

Previous production history remains in the source repository until full migration and deletion can be performed by an authorized repository administration operation.
