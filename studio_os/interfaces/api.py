from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import asyncio
import uuid
from typing import Optional

from ..core.orchestrator import Orchestrator, ProductionOrder, LoopType
from ..core.character_consistency import CanonicalCharacter

app = FastAPI(title="Studio OS", version="0.2.0")
orchestrator: Optional[Orchestrator] = None

class GenerateRequest(BaseModel):
    prompt: str
    lane: str = "series"  # series | farm | artist | platform
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

@app.on_event("startup")
async def startup():
    global orchestrator
    orchestrator = Orchestrator(comfyui_url="http://host.docker.internal:8188")
    # Start background workers (non-blocking)
    asyncio.create_task(orchestrator.start(num_workers=2))

@app.post("/generate")
async def generate(req: GenerateRequest):
    if not orchestrator:
        raise HTTPException(500, "Orchestrator not ready")
    try:
        loop = LoopType(req.lane)
    except ValueError:
        raise HTTPException(400, f"Unknown lane: {req.lane}")
    
    order = ProductionOrder(
        id=uuid.uuid4().hex,
        loop=loop,
        project_id=req.series_id or "default",
        prompt=req.prompt,
        character_id=req.character_id,
        series_id=req.series_id,
        episode_number=req.episode_number,
        duration_seconds=req.duration_seconds,
    )
    oid = await orchestrator.submit(order)
    return {"order_id": oid, "status": "queued"}

@app.get("/status/{order_id}")
async def status(order_id: str):
    if not orchestrator:
        raise HTTPException(500, "Not ready")
    for o in orchestrator.completed:
        if o.id == order_id:
            return {"status": "done", "output": str(o.output_path)}
    for o in orchestrator.failed:
        if o.id == order_id:
            return {"status": "failed", "error": o.error}
    if order_id in orchestrator.active:
        return {"status": "running"}
    raise HTTPException(404, "Unknown order ID")

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
    return {"id": c.id, "registered": True}

@app.get("/health")
async def health():
    return {"status": "ok", "comfyui": orchestrator.engine.comfyui_url if orchestrator else None}
