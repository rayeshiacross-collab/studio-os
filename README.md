# Studio OS

**Open-source multi-lane AI video production system with strict character consistency.**

Studio OS produces shorts, trailers, features, and series using free local open-source models (primarily **ComfyUI + Wan 2.2**). No paid APIs required.

> **For creators**: See [`docs/CREATOR_MANUAL.md`](docs/CREATOR_MANUAL.md) — simple step-by-step for making videos with locked characters.  
> **Canonical reference**: See [`docs/MANUAL.md`](docs/MANUAL.md) for principles, cost model, and decisions.

## Four Production Lanes

| Lane | Purpose | Concurrency | Approval | Consistency Focus |
|------|---------|-------------|----------|-------------------|
| **Artist** | High-quality feature films / premium content | 1 | Required | Highest |
| **Platform** | SaaS for authors (shorts/trailers) | 5 | Optional | High |
| **Farm** | High-volume shorts | 20 | None | Medium |
| **Series** | Multi-episode TV / YouTube series | 2 | Required | **Strict (locked characters)** |

## Character Consistency (Must-Have)

Every character has a **Canonical Character Profile**:
- Multiple reference images (face close-ups + full body)
- Optional trained LoRA (Wan 2.2 high-noise + low-noise)
- Locked identity embedding / reference conditioning passed to every generation
- Clothes and scene can change; face and core appearance do not

Handoffs between stages always re-anchor to the canonical references. Free-running agents are avoided for final output — controlled pipelines with quality gates.

## Stack

- **Rendering**: ComfyUI + Wan 2.2 (Apache 2.0, fully open, commercial-friendly)
- **Consistency**: Character LoRAs + reference image conditioning + face detailer passes
- **Orchestration**: Python (asyncio) with state machine, cost tracking, resource pool
- **API**: FastAPI
- **Ops**: Docker Compose, Woodpecker CI, optional Gitea for GPU job queueing

## Quick Start

```bash
# Requires NVIDIA GPU with sufficient VRAM for Wan 2.2 (16GB+ recommended)
docker compose up -d
```

See `docs/` for the creator manual, operations manual, character locking workflow, and series continuity rules.

## License

Open source. Use freely. Models follow their own licenses (Wan 2.2 is Apache 2.0).

---
Built from original submissions, updated for free open-source rendering and series-grade continuity.
