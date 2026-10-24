"""Offline tests for shared job store + approve flow (no ComfyUI)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio_os.core.job_store import JobStore
from studio_os.core.orchestrator import Orchestrator
from studio_os.core.character_consistency import CanonicalCharacter


class JobStoreTests(unittest.TestCase):
    def test_create_claim_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp))
            job = store.create(loop="farm", project_id="p", prompt="a cat walks")
            self.assertEqual(job.status, "queued")
            claimed = store.claim_next()
            self.assertIsNotNone(claimed)
            self.assertEqual(claimed.id, job.id)
            self.assertEqual(claimed.status, "running")
            claimed.output_path = "/tmp/out.mp4"
            store.update(claimed, new_status="done")
            got = store.get(job.id)
            self.assertEqual(got.status, "done")

    def test_uuid_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp))
            j1 = store.create(loop="farm", project_id="p", prompt="a")
            j2 = store.create(loop="farm", project_id="p", prompt="b")
            self.assertNotEqual(j1.id, j2.id)
            self.assertEqual(len(j1.id), 36)


class ApproveFlowTests(unittest.TestCase):
    def test_approve_requires_awaiting(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            orch = Orchestrator(job_store=JobStore(tmp / "jobs"), renders_dir=tmp / "renders")
            job = orch.store.create(
                loop="series", project_id="s1", prompt="walk",
                character_id="alice", series_id="s1", episode_number=1,
            )
            orch.store.update(job, new_status="awaiting_approval")
            orch.character_engine.register(
                CanonicalCharacter(id="alice", name="Alice", trigger_word="alice")
            )
            done = orch.approve(job.id)
            self.assertEqual(done.status, "done")


if __name__ == "__main__":
    unittest.main()
