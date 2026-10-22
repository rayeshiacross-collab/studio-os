"""Simple worker entry point."""
import asyncio
import os
from .core.orchestrator import Orchestrator

async def main():
    url = os.getenv("COMFYUI_URL", "http://localhost:8188")
    orch = Orchestrator(comfyui_url=url)
    print(f"[worker] Starting with ComfyUI at {url}")
    await orch.start(num_workers=2)

if __name__ == "__main__":
    asyncio.run(main())
