# Studio OS fixes (v0.3.0)

## Fixed in code

| Issue | Fix |
|-------|-----|
| API and worker used separate in-memory queues | **File-backed JobStore** under JOB_STORE_DIR |
| Order IDs from time() | **UUID4** |
| Series auto-approved after generate | **awaiting_approval** + **POST /approve/{order_id}** |
| Lane concurrency ignored | Claim only under per-lane max_concurrent |
| Health ignored ComfyUI | /health reports comfyui_reachable |
| Hardcoded Comfy URL | COMFYUI_URL env |

## Still requires the machine

1. ComfyUI + Wan 2.2 on host :8188
2. One successful generate → real mp4
3. Character refs / LoRAs on disk

## Tests

```bash
python -m unittest tests.test_job_store -v
```
