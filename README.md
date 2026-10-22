# Studio OS

**Open-source multi-lane AI video production system with strict character consistency.**

Studio OS produces shorts, trailers, features, and series using free local open-source models (primarily **ComfyUI + Wan 2.2**). No paid APIs required.

> **For creators**: See [`docs/CREATOR_MANUAL.md`](docs/CREATOR_MANUAL.md) — simple step-by-step for making videos with locked characters.  
> **Video editing**: See [`docs/VIDEO_EDITING.md`](docs/VIDEO_EDITING.md) — free/open-source editors to finish your clips.  
> **Canonical reference**: See [`docs/MANUAL.md`](docs/MANUAL.md) for principles, cost model, and decisions.

## Four Production Lanes

| Lane | Purpose | Concurrency | Approval | Consistency Focus |
|------|---------|-------------|----------|-------------------|
| **Artist** | High-quality feature films / premium content | 1 | Required | Highest |
| **Platform** | SaaS for authors (shorts/trailers) | 5 | Optional | High |
| **Farm** | High-volume shorts | 8 | None | Medium |
| **Series** | Multi-episode TV / YouTube series | 2 | Required | **Strict (locked characters)** |

## Character Consistency (Must-Have)

Every character has a **Canonical Character Profile**:
- Multiple reference images (face close-ups + full body)
- Optional trained LoRA (Wan 2.2 high-noise + low-noise)
- Locked identity embedding / reference conditioning passed to every generation
- Clothes and scene can change; face and core appearance do not

## Stack

- **Rendering**: ComfyUI + Wan 2.2 (Apache 2.0)
- **Consistency**: Character LoRAs + reference conditioning
- **Orchestration**: Async Python queue + Series continuity checks
- **API**: FastAPI (`/generate`, `/characters`, `/status/{id}`)
- **Ops**: Docker Compose (ComfyUI expected on host port 8188)

## Quick Start (Series or Farm ready)

1. Run ComfyUI on the host with Wan 2.2 models loaded (port 8188).
2. Clone and start Studio OS:

```bash
docker compose up -d --build
```

3. Register a character:

```bash
curl -X POST http://localhost:8000/characters \
  -H "Content-Type: application/json" \
  -d '{"id":"alice","name":"Alice","trigger_word":"char_alice_v1","reference_images":["./characters/alice/face1.jpg"],"lora_high_noise":"./models/alice_high.safetensors","lora_low_noise":"./models/alice_low.safetensors"}'
```

4. Generate a Series episode (or switch lane to `farm`):

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Alice walks through a rainy neon city at night, red jacket, determined","lane":"series","character_id":"alice","series_id":"veil_chronicles","episode_number":1,"duration_seconds":5}'
```

5. Check status: `curl http://localhost:8000/status/<order_id>`

Outputs land in `./renders/`. Series lane runs continuity checks and records approved baselines. Farm is for higher volume with looser gates.

## License

Open source. Use freely. Models follow their own licenses (Wan 2.2 is Apache 2.0).
