# Colab GPU runner — controlled setup

This is a proposed, non-automatic integration. No GPU instance is launched by GitHub Actions.

## Separation of responsibilities
- GitHub Actions: lint, tests, validation and packaging without a GPU.
- Colab: manual GPU jobs for Wan 2.2 and other model-dependent rendering.
- GitHub: source and reviewed small artifacts; do not commit weights, tokens, audio/video masters or large renders.
- Persistent model/output storage: explicitly mounted Google Drive, subject to available capacity.

## First run
1. Open https://colab.research.google.com and choose a GPU runtime.
2. In Colab Secrets, create `GITHUB_TOKEN` with read-only Contents permission on intended repositories. Enable notebook access. Do not paste it into a cell.
3. Execute the repository discovery/clone cell supplied in the setup conversation, or use authenticated `git clone` for this repository alone.
4. Verify `!nvidia-smi`, then install project-specific dependencies **only** for the selected project.
5. For Wan, check model sizes and GPU memory before downloading; a T4 does not guarantee that a Wan 2.2 configuration will fit.
6. Start ComfyUI on port 8188 only after installation and model checks; avoid exposing an unauthenticated Cloudflare tunnel to the public internet.
7. Test a short object/environment clip, export the **actual working** ComfyUI API workflow, and map its real node IDs in bindings.
8. Record pass/fail, workflow checksum, model versions, GPU type, output checksum and review status. Do not claim production readiness without a successful render.

## Security and reliability
- Never commit Colab secrets or embed tokens in clone URLs.
- Treat Colab as ephemeral; save only approved artifacts to persistent storage.
- Avoid blindly running setup scripts across all repositories: dependencies may conflict and GPU time is limited.
- A tunnel URL is not proof that Wan models loaded or that a video rendered.
- Keep repository updates in reviewable PRs; no automatic push to main.
