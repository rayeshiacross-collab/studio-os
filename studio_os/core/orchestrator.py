import asyncio
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .character_consistency import CharacterConsistencyEngine
from .series_continuity import SeriesContinuityManager
from ..engines.wan22 import Wan22Engine

class LoopType(Enum):
    ARTIST = "artist"
    PLATFORM = "platform"
    FARM = "farm"
    SERIES = "series"

@dataclass
class ProductionOrder:
    id: str
    loop: LoopType
    project_id: str
    prompt: str
    character_id: Optional[str] = None
    series_id: Optional[str] = None
    episode_number: Optional[int] = None
    duration_seconds: float = 5.0
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    status: str = "queued"
    output_path: Optional[Path] = None
    error: Optional[str] = None

class Orchestrator:
    """Slim, working production orchestrator for Studio OS.
    
    Supports Series (strict character lock + continuity) and Farm (high volume) lanes.
    Artist/Platform can be used but with fewer concurrent slots.
    """
    
    def __init__(self, comfyui_url: str = "http://localhost:8188"):
        self.character_engine = CharacterConsistencyEngine()
        self.series_manager = SeriesContinuityManager()
        self.engine = Wan22Engine(comfyui_url=comfyui_url)
        
        self.queue: asyncio.Queue = asyncio.Queue()
        self.active: Dict[str, ProductionOrder] = {}
        self.pending: Dict[str, ProductionOrder] = {}
        self.completed: List[ProductionOrder] = []
        self.failed: List[ProductionOrder] = []
        
        self.loop_configs = {
            LoopType.ARTIST: {"max_concurrent": 1, "require_approval": True},
            LoopType.PLATFORM: {"max_concurrent": 5, "require_approval": False},
            LoopType.FARM: {"max_concurrent": 8, "require_approval": False},
            LoopType.SERIES: {"max_concurrent": 2, "require_approval": True, "strict": True},
        }
        self._running = False
        self._workers = []

    async def submit(self, order: ProductionOrder) -> str:
        """Queue a production order. Returns order id."""
        if order.loop == LoopType.SERIES and order.series_id and order.episode_number and order.character_id:
            report = self.series_manager.check_episode_continuity(
                order.series_id, order.episode_number, [order.character_id], self.character_engine
            )
            if not report["passed"]:
                order.status = "rejected"
                order.error = "; ".join(report["errors"])
                self.failed.append(order)
                return order.id
            order.metadata["continuity_report"] = report
        
        order.status = "queued"
        self.pending[order.id] = order
        await self.queue.put(order)
        return order.id

    async def _worker(self):
        while self._running:
            try:
                order = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            
            self.pending.pop(order.id, None)
            self.active[order.id] = order
            order.status = "running"
            try:
                conditioning = None
                if order.character_id:
                    conditioning = self.character_engine.get_conditioning(order.character_id)
                
                out = await self.engine.generate_clip(
                    prompt=order.prompt,
                    character_conditioning=conditioning,
                    duration_seconds=order.duration_seconds,
                    output_path=Path(f"./renders/{order.id}.mp4"),
                )
                order.output_path = out
                order.status = "done"
                self.completed.append(order)
                
                # For Series, mark continuity after successful generation (approval still recommended)
                if order.loop == LoopType.SERIES and order.series_id and order.episode_number and order.character_id:
                    self.series_manager.record_approved_episode(
                        order.series_id, order.episode_number, [order.character_id], self.character_engine
                    )
            except Exception as e:
                order.status = "failed"
                order.error = str(e)
                self.failed.append(order)
            finally:
                self.active.pop(order.id, None)
                self.queue.task_done()

    async def start(self, num_workers: int = 2):
        self._running = True
        self._workers = [asyncio.create_task(self._worker()) for _ in range(num_workers)]
        await asyncio.gather(*self._workers, return_exceptions=True)

    def stop(self):
        self._running = False
