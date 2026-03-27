"""Signal routes — inspect agent signals and inject human signals."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.persistence import database as db

router = APIRouter(tags=["signals"])


class HumanSignalRequest(BaseModel):
    """Request body for human signal injection."""

    direction: str = Field(description="bullish, bearish, or neutral")
    magnitude: float = Field(ge=-1.0, le=1.0, description="Expected % move as decimal")
    confidence: float = Field(ge=0.0, le=0.95, description="Your confidence (0-0.95)")
    horizon: str = Field(description="Forecast horizon, e.g. 30d")
    evidence: list[dict] = Field(
        description="Supporting evidence: [{source, observation, relevance, timestamp}]"
    )
    risks: list[str] = Field(description="Key risks that could invalidate this signal")
    contrarian_note: str | None = Field(default=None, description="What the consensus might be missing")


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


@router.post("/forecasts/{run_id}/signals")
async def inject_human_signal(run_id: str, request: HumanSignalRequest) -> dict:
    """Inject a manual human analyst signal into a forecast run.

    The human signal is saved alongside AI agent signals and can be used
    in re-aggregation. The human_analyst agent is treated with a configurable
    weight (default: equal to the best-calibrated agent).

    Args:
        run_id: The forecast run to inject into.
        request: The human signal data.

    Returns:
        Confirmation with the saved signal ID.
    """
    await db.init_db()

    run = await db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    if request.direction not in ("bullish", "bearish", "neutral"):
        raise HTTPException(status_code=400, detail="direction must be bullish, bearish, or neutral")

    signal_id = await db.save_signal(
        run_id=run_id,
        agent_id="human_analyst",
        direction=request.direction,
        magnitude=request.magnitude,
        confidence=request.confidence,
        horizon=request.horizon,
        evidence=request.evidence,
        risks=request.risks,
        contrarian_note=request.contrarian_note,
        phase="human_injection",
    )

    # Also log for calibration tracking
    await db.save_calibration_entry(
        run_id=run_id,
        agent_id="human_analyst",
        asset=run["asset"],
        predicted_direction=request.direction,
        predicted_confidence=request.confidence,
    )

    return {
        "signal_id": signal_id,
        "agent_id": "human_analyst",
        "run_id": run_id,
        "status": "injected",
    }
