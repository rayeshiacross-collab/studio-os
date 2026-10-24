"""Studio OS FastAPI — shared job store, UUID orders, Series approve, ComfyUI health."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..core.character_consistency import CanonicalCharacter
from ..core.orchestrator import LoopType, Orchestrator

app = FastAPI(title="Studio OS", version="0.3.0")
orchestrator: Optional[Orchestrator] = None


class GenerateRequest(BaseModel):
    prompt: str
    lane: str = "series"
    character_id: Optional[str] = None
    series_id: Optional[str] = None
    episode_number: Optional[int] = None
    duration_seconds: float = 5.0


class CharacterRegister(BaseModel):
    id: str
    name: str
    trigger_word: str = ""
    reference_images: list[str] = []
    lora_high_noise: Optional[str] = None
    lora_low_noise: Optional[str] = None


def _comfy_url() -> str:
    return os.getenv("COMFYUI_URL", "http://host.docker.internal:8188").rstrip("/")


@app.on_event("startup")
async def startup():
    global orchestrator
    orchestrator = Orchestrator(comfyui_url=_comfy_url())
    asyncio.create_task(orchestrator.start(num_workers=int(os.getenv("API_WORKERS", "2"))))


@app.post("/generate")
async def generate(req: GenerateRequest):
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not ready")
    try:
        loop = LoopType(req.lane)
    except ValueError:
        raise HTTPException(400, f"Unknown lane: {req.lane}")
    job = await orchestrator.submit(
        loop=loop,
        project_id=req.series_id or "default",
        prompt=req.prompt,
        character_id=req.character_id,
        series_id=req.series_id,
        episode_number=req.episode_number,
        duration_seconds=req.duration_seconds,
    )
    return {"order_id": job.id, "status": job.status, "error": job.error}


@app.get("/status/{order_id}")
async def status(order_id: str):
    if not orchestrator:
        raise HTTPException(500, "Not ready")
    job = orchestrator.store.get(order_id)
    if not job:
        raise HTTPException(404, "Unknown order_id")
    return {
        "order_id": job.id,
        "status": job.status,
        "output": job.output_path,
        "error": job.error,
        "lane": job.loop,
    }


@app.post("/approve/{order_id}")
async def approve(order_id: str):
    if not orchestrator:
        raise HTTPException(500, "Not ready")
    try:
        job = orchestrator.approve(order_id)
    except KeyError:
        raise HTTPException(404, "Unknown order_id")
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"order_id": job.id, "status": job.status, "approved": True}


@app.post("/characters")
async def register_character(c: CharacterRegister):
    if not orchestrator:
        raise HTTPException(500, "Not ready")
    char = CanonicalCharacter(
        id=c.id,
        name=c.name,
        trigger_word=c.trigger_word,
        reference_images=[Path(p) for p in c.reference_images],
        lora_high_noise=Path(c.lora_high_noise) if c.lora_high_noise else None,
        lora_low_noise=Path(c.lora_low_noise) if c.lora_low_noise else None,
    )
    orchestrator.character_engine.register(char)
    return {"id": c.id, "registered": True, "identity_hash": char.identity_hash}


@app.get("/health")
async def health():
    comfy = _comfy_url()
    comfy_ok = False
    comfy_error = None
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{comfy}/system_stats")
            comfy_ok = r.status_code == 200
            if not comfy_ok:
                r2 = await client.get(f"{comfy}/")
                comfy_ok = r2.status_code < 500
    except Exception as e:
        comfy_error = str(e)
    return {
        "status": "ok",
        "version": "0.3.0",
        "comfyui_url": comfy,
        "comfyui_reachable": comfy_ok,
        "comfyui_error": comfy_error,
        "job_store": str(orchestrator.store.root) if orchestrator else None,
    }
