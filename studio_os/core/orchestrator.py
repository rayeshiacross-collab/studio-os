"""Production orchestrator — file-backed queue, lane caps, no auto Series approval."""
from __future__ import annotations

import asyncio
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from .character_consistency import CharacterConsistencyEngine
from .job_store import JobRecord, JobStore
from .series_continuity import SeriesContinuityManager
from ..engines.wan22 import Wan22Engine


class LoopType(Enum):
    ARTIST = "artist"
    PLATFORM = "platform"
    FARM = "farm"
    SERIES = "series"


LOOP_CONFIGS = {
    LoopType.ARTIST: {"max_concurrent": 1, "require_approval": True},
    LoopType.PLATFORM: {"max_concurrent": 5, "require_approval": False},
    LoopType.FARM: {"max_concurrent": 8, "require_approval": False},
    LoopType.SERIES: {"max_concurrent": 2, "require_approval": True, "strict": True},
}


class Orchestrator:
    def __init__(self, comfyui_url: str = "http://localhost:8188",
                 job_store: Optional[JobStore] = None,
                 renders_dir: Optional[Path] = None):
        self.character_engine = CharacterConsistencyEngine()
        self.series_manager = SeriesContinuityManager()
        self.engine = Wan22Engine(comfyui_url=comfyui_url)
        self.store = job_store or JobStore()
        self.renders_dir = Path(renders_dir or os.getenv("RENDERS_DIR", "./renders"))
        self.renders_dir.mkdir(parents=True, exist_ok=True)
        self.loop_configs = LOOP_CONFIGS
        self._running = False
        self._workers = []

    async def submit(self, *, loop: LoopType, project_id: str, prompt: str,
                     character_id: Optional[str] = None, series_id: Optional[str] = None,
                     episode_number: Optional[int] = None, duration_seconds: float = 5.0,
                     metadata: Optional[dict] = None) -> JobRecord:
        if loop == LoopType.SERIES and series_id and episode_number is not None and character_id:
            report = self.series_manager.check_episode_continuity(
                series_id, episode_number, [character_id], self.character_engine
            )
            if not report["passed"]:
                job = self.store.create(
                    loop=loop.value, project_id=project_id, prompt=prompt,
                    character_id=character_id, series_id=series_id,
                    episode_number=episode_number, duration_seconds=duration_seconds,
                    metadata={"continuity_report": report, **(metadata or {})},
                )
                job.error = "; ".join(report["errors"])
                return self.store.update(job, new_status="failed")
        return self.store.create(
            loop=loop.value, project_id=project_id, prompt=prompt,
            character_id=character_id, series_id=series_id,
            episode_number=episode_number, duration_seconds=duration_seconds,
            metadata=metadata or {},
        )

    async def process_job(self, job: JobRecord) -> JobRecord:
        try:
            conditioning = None
            if job.character_id:
                conditioning = self.character_engine.get_conditioning(job.character_id)
            out = await self.engine.generate_clip(
                prompt=job.prompt,
                character_conditioning=conditioning,
                duration_seconds=job.duration_seconds,
                output_path=self.renders_dir / f"{job.id}.mp4",
            )
            job.output_path = str(out)
            cfg = self.loop_configs.get(LoopType(job.loop))
            if cfg and cfg.get("require_approval"):
                return self.store.update(job, new_status="awaiting_approval")
            return self.store.update(job, new_status="done")
        except Exception as e:
            job.error = str(e)
            return self.store.update(job, new_status="failed")

    def approve(self, job_id: str) -> JobRecord:
        job = self.store.get(job_id)
        if not job:
            raise KeyError(f"Unknown job {job_id}")
        if job.status not in ("awaiting_approval", "done"):
            raise ValueError(f"Job {job_id} status is {job.status}, not awaiting_approval")
        if (job.loop == LoopType.SERIES.value and job.series_id
                and job.episode_number is not None and job.character_id):
            self.series_manager.record_approved_episode(
                job.series_id, job.episode_number, [job.character_id], self.character_engine
            )
        return self.store.update(job, new_status="done")

    async def _worker(self):
        while self._running:
            job = None
            for loop in LoopType:
                cfg = self.loop_configs[loop]
                if self.store.count_running(loop.value) >= cfg["max_concurrent"]:
                    continue
                job = self.store.claim_next(allowed_loops=[loop.value])
                if job:
                    break
            if not job:
                await asyncio.sleep(1.0)
                continue
            await self.process_job(job)

    async def start(self, num_workers: int = 2):
        self._running = True
        self._workers = [asyncio.create_task(self._worker()) for _ in range(num_workers)]
        await asyncio.gather(*self._workers, return_exceptions=True)

    def stop(self):
        self._running = False
