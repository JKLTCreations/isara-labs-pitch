"""WebSocket route for live forecast progress streaming."""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.deps import event_stream, get_run_queue
from src.persistence import database as db

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/forecast/{run_id}")
async def forecast_ws(websocket: WebSocket, run_id: str) -> None:
    """Stream live forecast progress for a run.

    Events:
        agent_complete — An agent finished and produced a signal.
        debate_round — A debate round completed.
        forecast_complete — The aggregator produced the final forecast.
        run_failed — The run encountered an error.
    """
    await websocket.accept()

    try:
        async for event in event_stream(run_id):
            await websocket.send_text(json.dumps(event, default=str))
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
