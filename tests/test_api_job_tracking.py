import asyncio
import pytest
from fastapi import HTTPException
from studio_os.interfaces import api
from studio_os.core.orchestrator import Orchestrator, ProductionOrder, LoopType


def test_unique_order_ids():
    import uuid
    assert uuid.uuid4().hex != uuid.uuid4().hex


def test_unknown_order_is_404():
    async def check():
        original = api.orchestrator
        api.orchestrator = Orchestrator()
        try:
            with pytest.raises(HTTPException) as exc:
                await api.status("not-a-real-order")
            assert exc.value.status_code == 404
        finally:
            await api.orchestrator.engine.close()
            api.orchestrator = original
    asyncio.run(check())


def test_pending_order_status():
    async def check():
        original = api.orchestrator
        api.orchestrator = Orchestrator()
        try:
            order = ProductionOrder(id="pending-1", loop=LoopType.FARM, project_id="test", prompt="test")
            await api.orchestrator.submit(order)
            assert (await api.status(order.id))["status"] == "queued"
        finally:
            await api.orchestrator.engine.close()
            api.orchestrator = original
    asyncio.run(check())
