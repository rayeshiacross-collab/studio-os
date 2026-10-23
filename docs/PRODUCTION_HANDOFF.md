# Studio OS production handoff
Status: **unverified** until CI, host preflight, and a rendered clip pass.

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
