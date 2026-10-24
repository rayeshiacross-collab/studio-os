"""File-backed job store shared by API and worker processes."""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class JobRecord:
    id: str
    loop: str
    project_id: str
    prompt: str
    character_id: Optional[str] = None
    series_id: Optional[str] = None
    episode_number: Optional[int] = None
    duration_seconds: float = 5.0
    priority: int = 0
    status: str = "queued"
    output_path: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "JobRecord":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})


class JobStore:
    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root or os.getenv("JOB_STORE_DIR", "./job_store"))
        for sub in ("queued", "running", "done", "failed", "awaiting_approval"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    def _path(self, status: str, job_id: str) -> Path:
        return self.root / status / f"{job_id}.json"

    def _write(self, job: JobRecord) -> None:
        job.updated_at = _now()
        self._path(job.status, job.id).write_text(
            json.dumps(job.to_dict(), indent=2), encoding="utf-8"
        )

    def _remove_other_statuses(self, job_id: str, keep: str) -> None:
        for st in ("queued", "running", "done", "failed", "awaiting_approval", "rejected"):
            if st == keep:
                continue
            p = self.root / st / f"{job_id}.json"
            if p.exists():
                p.unlink()

    def create(self, **kwargs) -> JobRecord:
        job_id = kwargs.pop("id", None) or str(uuid.uuid4())
        job = JobRecord(id=job_id, status="queued", **kwargs)
        self._write(job)
        return job

    def get(self, job_id: str) -> Optional[JobRecord]:
        for st in ("queued", "running", "done", "failed", "awaiting_approval", "rejected"):
            p = self._path(st, job_id)
            if p.is_file():
                return JobRecord.from_dict(json.loads(p.read_text(encoding="utf-8")))
        return None

    def update(self, job: JobRecord, new_status: Optional[str] = None) -> JobRecord:
        if new_status and new_status != job.status:
            job.status = new_status
            self._remove_other_statuses(job.id, keep=new_status)
        self._write(job)
        return job

    def claim_next(self, allowed_loops: Optional[List[str]] = None) -> Optional[JobRecord]:
        qdir = self.root / "queued"
        files = sorted(qdir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        for path in files:
            try:
                job = JobRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
                if allowed_loops and job.loop not in allowed_loops:
                    continue
                running = self.root / "running" / path.name
                path.rename(running)
                job.status = "running"
                job.updated_at = _now()
                running.write_text(json.dumps(job.to_dict(), indent=2), encoding="utf-8")
                return job
            except (FileNotFoundError, OSError, json.JSONDecodeError):
                continue
        return None

    def count_running(self, loop: Optional[str] = None) -> int:
        n = 0
        for p in (self.root / "running").glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if loop is None or d.get("loop") == loop:
                    n += 1
            except (OSError, json.JSONDecodeError):
                continue
        return n
