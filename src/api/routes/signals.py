"""Signal routes — inspect agent signals for a forecast run."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from src.persistence import database as db

router = APIRouter(tags=["signals"])


@router.get("/forecasts/{run_id}/signals")
async def get_run_signals(run_id: str) -> dict:
    """Get all agent signals for a specific forecast run."""
    await db.init_db()

    run = await db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    signals = await db.get_signals(run_id)

    for s in signals:
        s["evidence"] = json.loads(s.get("evidence_json", "[]"))
        s["risks"] = json.loads(s.get("risks_json", "[]"))
        s.pop("evidence_json", None)
        s.pop("risks_json", None)

    return {"run_id": run_id, "signals": signals, "count": len(signals)}


@router.get("/forecasts/{run_id}/signals/{agent_id}")
async def get_agent_signal(run_id: str, agent_id: str) -> dict:
    """Get a single agent's signals for a run with full evidence."""
    await db.init_db()

    run = await db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    signals = await db.get_signals(run_id, agent_id=agent_id)
    if not signals:
        raise HTTPException(
            status_code=404,
            detail=f"No signals from {agent_id} in run {run_id}",
        )

    for s in signals:
        s["evidence"] = json.loads(s.get("evidence_json", "[]"))
        s["risks"] = json.loads(s.get("risks_json", "[]"))
        s.pop("evidence_json", None)
        s.pop("risks_json", None)

    return {"run_id": run_id, "agent_id": agent_id, "signals": signals}
