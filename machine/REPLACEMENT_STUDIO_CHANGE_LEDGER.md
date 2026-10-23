# Machine change ledger — 2026-10-23

## Studio repair continuation — 2026-10-23
Owner instruction: repair/backup work only; all production remains stopped. This entry adds current evidence without replacing earlier records.

Baseline: `3b22dacc2739075d830bc3629e01b211b842a5ef` on `fix/api-job-status-health-20261023`. GitHub run `39980403020` completed successfully, including its regression-test step. Its workflow only selected the API tracking test file, so it did not establish media/host readiness.

Changes prepared: strict read-only Python preflight (required media tools, Python dependency checks, explicit Compose/native mode, bounded renderer JSON requests without proxy/redirects, workflow class/model inventory); shell wrapper anchored to repo root; renderer clients no longer inherit proxy settings; all test files selected by CI; service-starting smoke workflow changed to manual-only during owner hold. No runtime startup or render submitted.

Validation: 16 local tests passed, including synthetic media/fixture-server tests and seven preflight/proxy tests. Python compilation, pip check, bash syntax and diff checks passed. Existing FastAPI startup deprecation warnings remain. No rendering host, GPU capacity or live output verified. Hermes startup remains a separate unresolved issue. Source checks cannot certify full production readiness.

Detailed next steps and limits: `docs/PRODUCTION_HANDOFF.md`. Continue from the repair branch; do not overwrite shared main or modify the four manual workers. The private backup destination was previously made private, but its code upload has not been verified here. Prior scratch/runtime files were removed by automated workspace maintenance; this source was re-cloned from GitHub.

## Owner decision (authorized plan; not completed)
- RETIRE AND DELETE: `rayeshiacross-collab/rebootv2-autopilot`. Owner explicitly requests repository destruction, not merely disabling the workflow. **Deletion NOT executed**: connector lacks repository deletion.
- KEEP: the large Studio and existing smaller Studio unchanged.
- CREATE: an independent **third Studio**, cloning the smaller Studio rather than adding a lane to the existing Studio. **Clone NOT executed**: connector lacks repository creation/clone.
- Visual rules for the replacement: **plain, realistic human-looking people**, natural faces/movement/expression; no imposed red/pink styling, custom lines, borders, overlays, or cyberpunk branding.
- Owner will supply further research and additions later. Do not preemptively customize or add unapproved capabilities.
- EP11 owner-provided videos/audio are reference assets. Preserve originals, use owner-selected audio; do not substitute synthetic narration. Do not publish without owner seeing/hearing and approving.

## Confirmed source Studio capabilities (code/docs, not runtime certification)
Source repository: `rayeshiacross-collab/studio-os`.
- ComfyUI / Wan 2.2 video engine integration, using `/prompt`, `/history`, and video download.
- FastAPI `/generate`, `/characters`, `/status/{order_id}`, `/health`.
- Asynchronous job queue and workers.
- Artist, Platform, Farm, Series lanes; Series has character-consistency and continuity checks.
- Character profiles, reference images, optional LoRA conditioning.
- Docker Compose API and worker services.
- Motion batch pipeline for **object/environment scenes only**, requiring a tested Wan API graph/bindings and available ComfyUI worker; rejects static outputs and preserves receipt/checksum and no-publish status.
- Existing source Studio requires an external running ComfyUI/Wan installation; no verified live engine, successful render, or deployed clone established by this ledger.

## Execution status
| Operation | Status |
| --- | --- |
| Owner's replacement instructions recorded | DONE |
| Old EP11 GitHub Actions workflow disabled | DONE (prior change) |
| Old repository deleted | NOT DONE |
| Independent clone created | NOT DONE |
| Clone deployed / video render tested | NOT DONE |
| EP11 published | NO; owner review required |

## Operating safeguards
Keep all existing Studios untouched. Do not interpret a new folder, intake file, commit, or passing synthetic test as a cloned and deployed studio. Once repository admin operations become available, create the independent copy, verify the copy's code/engine/health, migrate only owner-approved assets, and then delete the old repo as explicitly instructed.


Maintenance handoff signed: **Rip — ChatGPT/Codex**, 2026-10-23. Owner approved uploading this repair and its machine notes to the public shared Studio OS repository. Signature is a handoff label, not a cryptographic commit signature. Production hold remains in effect.
