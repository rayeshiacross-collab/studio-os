# Studio OS production handoff
Status: **unverified** until CI, host preflight, and a rendered clip pass.

## Maintenance handoff — 2026-10-23
The owner is holding all production runs. Do not start services or submit a clip as part of this repair.

- Baseline reviewed: `3b22dacc2739075d830bc3629e01b211b842a5ef`, branch `fix/api-job-status-health-20261023`.
- GitHub CI run `39980403020` passed for that baseline, but ran only `tests/test_api_job_tracking.py`. That green check does not cover the media pipeline or certify a rendering host.
- This repair expands CI to the complete test directory and checks that FFmpeg/ffprobe are installed. CI uses synthetic media and a fixture server, never Wan inference.
- Startup smoke workflow is now manual-only. Do not dispatch it while the production hold is in effect. It still requires a reachable ComfyUI backend; a generic hosted runner without that backend will not pass it.
- Renderer HTTP clients ignore inherited proxies and do not follow redirects. TLS verification remains enabled.
- `bash scripts/preflight.sh` now fails on missing FFmpeg, ffprobe, Docker/Compose, broken Python dependencies, invalid renderer inventory, missing workflow classes, or model filenames absent from renderer inventory. Use `--native` only for an intentional non-Docker host. Use `--workflow PATH` for the actual configured graph.
- Preflight uses GET requests only, never starts services, and never submits a prompt. Success means `PREREQUISITES_VERIFIED`; `render_verified` and `production_ready` remain false. This does not prove GPU capacity, graph compatibility, character fidelity, motion, audio, or review quality.
- No actual rendering host was identified or contacted for this repair. Docker is absent in this workspace. The previous Hermes gateway bootstrap blocker is separate and remains unresolved.

Validation for this repair: 16 local tests passed (9 existing plus 7 preflight/proxy regression tests); pip check, Python compilation, shell syntax, and diff checks passed. Two existing FastAPI startup deprecation warnings remain.

Next operator: review these changes and their CI; identify the real rendering host and its available disk/GPU memory; perform the read-only host preflight there only when the owner authorizes that check. Preserve the failed receipt if it does not pass. Keep the four manual production workers and main branch unchanged. A live clip and owner review remain later gates, after the hold is lifted.

## Free/open-source stack
- Studio OS: Python/FastAPI orchestration
- ComfyUI + Wan 2.2: video rendering, requires a separately provisioned compatible GPU host and model weights
- FFmpeg: media validation and assembly
- Docker Compose: services
- GitHub Actions: source checks and tests, **not** video GPU rendering

## Startup gate
1. Review and pass GitHub CI.
2. Identify rendering host and available disk/GPU memory.
3. Install ComfyUI, licensed model weights, FFmpeg, and Docker as needed on that host.
4. Set COMFYUI_URL to the reachable endpoint.
5. Run bash scripts/preflight.sh on the host.
6. Submit a short internal test clip; confirm file exists, has motion and audio as applicable, and plays.
7. Record result, host, commit, artifact path and review status in shared ledger.
8. Only after owner review, promote to main and integrate with Big One.

No generated content is authorized for public release by this document. Other manual content workers remain independent.


Maintenance handoff signed: **Rip — ChatGPT/Codex**, 2026-10-23. Owner approved uploading this repair and its machine notes to the public shared Studio OS repository. Signature is a handoff label, not a cryptographic commit signature. Production hold remains in effect.
