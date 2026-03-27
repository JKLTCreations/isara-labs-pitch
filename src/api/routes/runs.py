"""Run routes — list orchestration runs, inspect debates, and view calibration."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from src.persistence import database as db
from src.signals.calibration import get_calibration_profile

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("")
async def list_runs(
    asset: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List all orchestration runs with status and timing."""
    await db.init_db()

    runs = await db.list_runs(asset=asset, status=status, limit=limit, offset=offset)
    total = await db.count_runs(asset=asset, status=status)

    return {
        "runs": runs,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# Calibration routes MUST come before /{run_id} to avoid path collision
@router.get("/calibration")
async def get_calibration_dashboard() -> dict:
    """Get calibration profiles for all agents with historical data."""
    await db.init_db()

    summaries = await db.get_all_calibration_profiles()

    # Enrich with full calibration profiles
    profiles = []
    for summary in summaries:
        agent_id = summary["agent_id"]
        profile = await get_calibration_profile(agent_id)
        profiles.append({
            "agent_id": agent_id,
            "total_predictions": profile.total_predictions,
            "overall_accuracy": profile.overall_accuracy,
            "calibration_weight": profile.calibration_weight,
            "platt_params": profile.platt_params,
            "buckets": profile.buckets,
        })

    return {"profiles": profiles, "count": len(profiles)}


@router.get("/calibration/{agent_id}")
async def get_agent_calibration_detail(agent_id: str, asset: str | None = None) -> dict:
    """Get detailed calibration profile for a specific agent."""
    await db.init_db()

    profile = await get_calibration_profile(agent_id, asset)

    return {
        "agent_id": agent_id,
        "asset": asset,
        "total_predictions": profile.total_predictions,
        "overall_accuracy": profile.overall_accuracy,
        "calibration_weight": profile.calibration_weight,
        "platt_params": profile.platt_params,
        "buckets": profile.buckets,
    }


@router.get("/{run_id}")
async def get_run(run_id: str) -> dict:
    """Get details for a single run."""
    await db.init_db()

    run = await db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return {"run": run}


@router.get("/{run_id}/debate")
async def get_debate_transcript(run_id: str) -> dict:
    """Get the full debate transcript for a run."""
    await db.init_db()

    run = await db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    debates = await db.get_debates(run_id)

    # Group by round
    rounds: dict[int, list[dict]] = {}
    for d in debates:
        rn = d["round_number"]
        rounds.setdefault(rn, []).append(d)

    return {
        "run_id": run_id,
        "total_rounds": len(rounds),
        "rounds": rounds,
        "exchanges": debates,
    }


@router.get("/{run_id}/trace")
async def get_run_trace(run_id: str) -> dict:
    """Get agent execution trace for a run (timing, signals per phase)."""
    await db.init_db()

    run = await db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    signals = await db.get_signals(run_id)
    debates = await db.get_debates(run_id)
    calibration = await db.get_calibration_for_run(run_id)

    # Parse JSON fields in signals
    for s in signals:
        s["evidence"] = json.loads(s.get("evidence_json", "[]"))
        s["risks"] = json.loads(s.get("risks_json", "[]"))
        s.pop("evidence_json", None)
        s.pop("risks_json", None)

    # Group signals by phase
    phases: dict[str, list[dict]] = {}
    for s in signals:
        phase = s.get("phase", "initial")
        phases.setdefault(phase, []).append(s)

    # Group agents
    agents: dict[str, dict] = {}
    for s in signals:
        aid = s["agent_id"]
        if aid not in agents:
            agents[aid] = {"agent_id": aid, "signal_count": 0, "phases": []}
        agents[aid]["signal_count"] += 1
        agents[aid]["phases"].append(s.get("phase", "initial"))

    return {
        "run_id": run_id,
        "run": run,
        "elapsed_seconds": run.get("elapsed_seconds"),
        "agent_count": run.get("agent_count"),
        "debate_rounds": run.get("debate_rounds"),
        "phases": {phase: len(sigs) for phase, sigs in phases.items()},
        "agents": list(agents.values()),
        "signals": signals,
        "debate_exchanges": len(debates),
        "calibration_entries": len(calibration),
    }
