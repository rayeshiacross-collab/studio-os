# Studio OS Operations Manual

**Canonical reference for principles, costs, architecture, and operations.**  
Everything in this document is the current agreed direction unless explicitly updated.

---

## Core Principles

1. **Open-source and free wherever possible.** Prefer local models and tools. No paid generation APIs.
2. **Character consistency is non-negotiable.** The person cannot change. Clothes, hair styling, and scene can. Face and core identity stay locked across all content (shorts, series, features).
3. **Controlled pipelines over free-running agents.** Handoffs must re-anchor to canonical character references. Quality control and continuity are harder with autonomous agents, so we avoid them for final output.
4. **Four production lanes** (not three):
   - **Artist** — High-quality / premium (low concurrency, approval required)
   - **Platform** — SaaS-style shorts/trailers
   - **Farm** — High-volume shorts
   - **Series** — Multi-episode TV / YouTube series (strict continuity, approval required)
5. **Virtually free is the goal.** Ongoing monthly cost should stay as close to $0 as possible. Cloud is optional and used sparingly.

---

## Rendering Stack (Current)

- **Primary**: ComfyUI + **Wan 2.2** (Apache 2.0 license — commercial-friendly, fully open weights).
- Character locking via:
  - Canonical reference images
  - Trained high-noise + low-noise LoRAs
  - Trigger words + reference conditioning passed on every generation
- Workflow example: `workflows/wan22_character_locked_t2v.json`

Smaller / quantized variants (5B, FP8, GGUF, etc.) are preferred when VRAM is limited so local hardware remains usable.

---

## Cost Model & Free Path

### Target
Virtually free ongoing cost. Hardware ownership is the path to $0/month.

### Virtually Free (Recommended Default)
| Component | Solution | Ongoing Cost |
|-----------|----------|--------------|
| Compute | Local NVIDIA GPU (12–24 GB VRAM used or new) | $0 |
| Storage | Local NVMe/SSD (500 GB–1 TB) | $0 |
| Models | Wan 2.2 (download once) + local LoRAs | $0 |
| Orchestration | This repo (Python) | $0 |
| Occasional testing | Hugging Face Spaces ZeroGPU, Colab free, Kaggle | $0 (limited/queued) |

**Minimum practical local hardware**: Used RTX 3060 12GB, 3090, 4070 Ti, or better. Quantized Wan 2.2 works on 12 GB cards for shorter clips.

### Light Cloud (Optional, When Local Is Unavailable)
- Tooling example: CloudsForge ($49 one-time desktop app) + RunPod or Vast.ai.
- GPU time only when generating. Shut instances down when idle.
- Shared RunPod network volume for models (~$0.07/GB/month). 80–100 GB ≈ $6–7/month.
- Realistic monthly range for moderate posting volume with tight approval gates: **$10–20**.
- Prefer Vast.ai for cheapest short bursts; RunPod for more reliable persistent storage.

### What We Avoid
- Paid closed APIs (Runway, Kling, etc.)
- Always-on cloud GPU instances
- Free-running agents that generate final video without gates

---

## Storage Guidance

- **Active models + LoRAs**: Keep local or on a single persistent volume. Do not re-download constantly.
- **Finished outputs**: Download locally or move to cheap object storage (Cloudflare R2 free tier, Hugging Face private datasets, or local archive).
- Comfortable starting size: 80–150 GB for models + working space.
- Local disk is always preferred for the zero-cost goal.

---

## Series & Continuity Rules (Summary)

See also `docs/series_continuity.md` and `docs/character_consistency.md`.

- Register every character in `CharacterConsistencyEngine` **before** episode 1.
- Same identity hash across all episodes. Changing references or LoRA creates a new hash and fails the check.
- Clothes and styling may change; face and core identity may not.
- `SeriesContinuityManager.check_episode_continuity()` must pass before generation.
- Human approval required before recording the episode baseline for the next one.

---

## Current Status & Open Items

- Architecture and core modules are in the repo.
- Group is still brainstorming exact hardware vs light-cloud mix.
- Preference is strongly toward open-source + free / local-first.
- Collaborators are still contributing input; this manual will be updated as decisions firm up.

---

## Quick Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-10-19 | Expand to 4 lanes (add Series) | Continuity for multi-episode content is hard; needs dedicated path |
| 2026-10-19 | No free-running agents for final output | Quality control and character consistency suffer |
| 2026-10-19 | Wan 2.2 + ComfyUI as primary renderer | Fully open (Apache 2.0), strong quality, LoRA ecosystem |
| 2026-10-19/20 | Prefer local hardware for virtually free operation | Cloud GPU time becomes the dominant cost at volume |
| 2026-10-20 | Document cost ranges and free path in this manual | Keep the team aligned on constraints |

---

*This manual is the canonical reference. Update it when principles, stack, or cost assumptions change.*
