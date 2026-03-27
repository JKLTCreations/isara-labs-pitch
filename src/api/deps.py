"""Shared dependencies for the API layer."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from src.config import get_config
from src.persistence import database as db

# In-flight forecast runs tracked for WebSocket progress
_active_runs: dict[str, asyncio.Queue[dict[str, Any]]] = {}


def get_run_queue(run_id: str) -> asyncio.Queue[dict[str, Any]]:
    """Get or create the event queue for a forecast run."""
    if run_id not in _active_runs:
        _active_runs[run_id] = asyncio.Queue()
    return _active_runs[run_id]


def remove_run_queue(run_id: str) -> None:
    """Clean up the event queue after a run completes."""
    _active_runs.pop(run_id, None)


async def emit_event(run_id: str, event: dict[str, Any]) -> None:
    """Push an event to the run's queue (if anyone is listening)."""
    queue = _active_runs.get(run_id)
    if queue:
        await queue.put(event)


async def event_stream(run_id: str) -> AsyncGenerator[dict[str, Any], None]:
    """Async generator that yields events for a run."""
    queue = get_run_queue(run_id)
    while True:
        event = await queue.get()
        yield event
        if event.get("event") in ("forecast_complete", "run_failed"):
            break
