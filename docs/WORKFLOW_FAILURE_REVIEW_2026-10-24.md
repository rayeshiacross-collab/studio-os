# Studio OS workflow failure review — October 24, 2026

Repository: rayeshiacross-collab/studio-os. No merge, deployment, file deletion, or visibility change performed.

## CI #6 — preflight CI handoff

Run: https://github.com/rayeshiacross-collab/studio-os/actions/runs/39981873272

The `Verify fixture media tools` step ran `command -v ffmpeg && command -v ffprobe` and exited 1. Compilation and regression tests were skipped. Python package installation does not install these system binaries.

Existing draft PR #3 installs the Ubuntu `ffmpeg` package (which supplies both tools) before checking them. Its CI #7 passed:
https://github.com/rayeshiacross-collab/studio-os/actions/runs/39984900024

This repair is based on that existing fix, commit `22133e9945663801103339cb415142b509a9afaa`, rather than duplicating it.

## Startup smoke #6 — API job-status health

Run: https://github.com/rayeshiacross-collab/studio-os/actions/runs/39972704076

Both Docker services built and started. The API's real ComfyUI reachability check returned 503 on every `/health` request because the hosted runner had no renderer at the configured host address. The smoke workflow still expected the former unconditional 200/`status=ok` contract. `curl --fail` suppressed the 503 response body, so its eventual JSONDecodeError was a secondary symptom.

Correction:
- Keep the real API health behavior unchanged.
- Use a test-only Compose override that forces the renderer URL to loopback port 1, for both API and worker. No real renderer is contacted by this boot test.
- Check the exact 503 degraded/unreachable contract, preserving error response bodies and using bounded requests/retries.
- Reject unrelated 503 errors, malformed bodies, and unexpected status/body combinations.
- Retain the workflow packaging and character-registration checks.
- Preserve manual-only dispatch and the production hold. A boot check is not a renderer-readiness check. The checker supports an explicit `--expect-comfyui reachable` check for later authorized readiness verification; neither mode proves an actual render.

## Validation

- Existing baseline suite: 16 passed.
- Complete suite with six new HTTP/ASGI regression tests: 22 passed, two existing FastAPI startup deprecation warnings.
- Python compilation, pip dependency check, preflight shell syntax, and whitespace checks passed.
- Local Python is 3.12; the existing GitHub CI selects Python 3.11.
- Docker is unavailable in this workspace: corrected Docker boot workflow has not been executed here. No manual workflow dispatch, production service startup, or inference request was made.
- GitHub CI for this repair must be read separately after opening the draft PR.

## Shared work and messages

Checked all three existing PR conversations/reviews, repository-wide issue comments and commit comments: no comments were present at inspection. Read the signed Rip maintenance handoff on the preflight branch. Kept the existing repair branches and the separate v0.3 hardening branch intact. This patch targets the FFmpeg repair branch and does not reconcile or merge those branches.
