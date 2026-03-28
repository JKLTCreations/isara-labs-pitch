"""Forecast routes — trigger new forecasts and retrieve results."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from src.api.deps import emit_event, remove_run_queue
from src.orchestrator.multi_swarm import run_multi_swarm
from src.orchestrator.swarm import run_swarm
from src.persistence import database as db

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


class ForecastRequest(BaseModel):
    asset: str = Field(description="Asset to forecast, e.g. XAUUSD, CL1, SPX")
    horizon: str = Field(default="30d", description="Forecast horizon, e.g. 7d, 30d, 90d")
    agents: list[str] | None = Field(default=None, description="Specific agents to run (overrides triage)")
    context: str | None = Field(default=None, description="Context for triage agent selection, e.g. 'election impact on gold'")
    skip_debate: bool = Field(default=False, description="Skip adversarial debate rounds")
    correlated: bool = Field(default=False, description="Run parallel swarms for correlated assets")


class ForecastTriggerResponse(BaseModel):
    run_id: str
    status: str


async def _run_forecast_task(
    run_id: str,
    asset: str,
    horizon: str,
    agents: list[str] | None,
    context: str | None,
    skip_debate: bool,
    correlated: bool,
) -> None:
    """Background task that runs the swarm and emits progress events."""
    try:
        if correlated:
            multi_result = await run_multi_swarm(
                asset=asset,
                horizon=horizon,
                context=context,
                persist=True,
                run_id=run_id,
            )
            result = multi_result.primary_result

            # Emit correlated results
            for corr_asset, corr_result in multi_result.correlated_results.items():
                if corr_result.forecast:
                    await emit_event(run_id, {
                        "event": "correlated_forecast",
                        "asset": corr_asset,
                        "forecast": corr_result.forecast.model_dump(),
                    })

            # Emit cross-swarm conflicts
            if multi_result.cross_swarm_conflicts:
                await emit_event(run_id, {
                    "event": "cross_swarm_conflicts",
                    "conflicts": multi_result.cross_swarm_conflicts,
                    "notes": multi_result.correlation_notes,
                })
        else:
            result = await run_swarm(
                asset=asset,
                horizon=horizon,
                agent_ids=agents,
                context=context,
                skip_debate=skip_debate,
                persist=True,
                run_id=run_id,
            )

        # Emit agent completion events
        for signal in result.signals:
            await emit_event(run_id, {
                "event": "agent_complete",
                "agent": signal.agent_id,
                "signal": signal.model_dump(),
            })

        # Emit debate round events
        for dr in result.debate_rounds:
            await emit_event(run_id, {
                "event": "debate_round",
                "round": dr.round_number,
                "challenges": [c.model_dump() for c in dr.challenges],
                "revisions": [r.model_dump() for r in dr.revisions],
            })

        # Emit final result
        if result.forecast:
            await emit_event(run_id, {
                "event": "forecast_complete",
                "forecast": result.forecast.model_dump(),
            })
        else:
            await emit_event(run_id, {
                "event": "run_failed",
                "errors": result.errors,
            })

    except Exception as e:
        await emit_event(run_id, {
            "event": "run_failed",
            "errors": [str(e)],
        })
    finally:
        # Clean up after a delay so WebSocket clients can read the final event
        await asyncio.sleep(5)
        remove_run_queue(run_id)


@router.post("", response_model=ForecastTriggerResponse, status_code=202)
async def create_forecast(
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
) -> ForecastTriggerResponse:
    """Trigger a new forecast run. Processes asynchronously and returns the run ID."""
    await db.init_db()
    agent_count = len(request.agents) if request.agents else 4
    run_id = await db.create_run(request.asset, request.horizon, agent_count)

    background_tasks.add_task(
        _run_forecast_task,
        run_id,
        request.asset,
        request.horizon,
        request.agents,
        request.context,
        request.skip_debate,
        request.correlated,
    )

    return ForecastTriggerResponse(run_id=run_id, status="running")


@router.get("/{forecast_id}")
async def get_forecast(forecast_id: str) -> dict:
    """Get a completed forecast by run ID with full signal chain and debate summary."""
    await db.init_db()

    run = await db.get_run(forecast_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {forecast_id} not found")

    forecast = await db.get_forecast(forecast_id)
    signals = await db.get_signals(forecast_id)
    debates = await db.get_debates(forecast_id)

    # Parse JSON fields
    for s in signals:
        s["evidence"] = json.loads(s.get("evidence_json", "[]"))
        s["risks"] = json.loads(s.get("risks_json", "[]"))
        s.pop("evidence_json", None)
        s.pop("risks_json", None)

    if forecast:
        forecast["key_drivers"] = json.loads(forecast.get("key_drivers_json", "[]"))
        forecast["key_risks"] = json.loads(forecast.get("key_risks_json", "[]"))
        forecast.pop("key_drivers_json", None)
        forecast.pop("key_risks_json", None)

    return {
        "run": run,
        "forecast": forecast,
        "signals": signals,
        "debates": debates,
    }


@router.get("")
async def list_forecasts(
    asset: str | None = None,
    conviction: str | None = None,
    limit: int = 50,
    offset: int = 0,
    dedupe: bool = True,
) -> dict:
    """List all forecasts with pagination and filters.

    When dedupe=True (default), only the latest forecast per asset+horizon
    is returned to avoid duplicate predictions on the dashboard.
    """
    await db.init_db()

    forecasts = await db.list_forecasts(
        asset=asset, conviction=conviction, limit=limit, offset=offset,
    )

    # Parse JSON fields
    for f in forecasts:
        f["key_drivers"] = json.loads(f.get("key_drivers_json", "[]"))
        f["key_risks"] = json.loads(f.get("key_risks_json", "[]"))
        f.pop("key_drivers_json", None)
        f.pop("key_risks_json", None)

    # Deduplicate: keep only the latest forecast per asset+horizon
    if dedupe:
        seen: dict[str, dict] = {}
        for f in forecasts:
            key = f"{f['asset']}:{f['horizon']}"
            if key not in seen:
                seen[key] = f
        forecasts = list(seen.values())

    return {
        "forecasts": forecasts,
        "count": len(forecasts),
        "limit": limit,
        "offset": offset,
    }
