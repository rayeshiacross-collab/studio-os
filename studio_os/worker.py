"""Worker process — drains the shared file-backed job store."""
from __future__ import annotations

import asyncio
import os

from .core.orchestrator import Orchestrator


async def main():
    url = os.getenv("COMFYUI_URL", "http://localhost:8188")
    workers = int(os.getenv("NUM_WORKERS", "2"))
    orch = Orchestrator(comfyui_url=url)
    print(f"[worker] ComfyUI={url} job_store={orch.store.root} workers={workers}")
    await orch.start(num_workers=workers)


if __name__ == "__main__":
    asyncio.run(main())
