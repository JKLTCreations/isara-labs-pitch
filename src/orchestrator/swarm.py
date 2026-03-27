"""Swarm orchestrator — full pipeline: parallel analysis → debate → aggregation.

All runs, signals, debates, and forecasts are persisted to SQLite.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from agents import Agent, Runner

from src.agents.aggregator import build_aggregator_prompt, create_aggregator_agent
from src.agents.registry import create_swarm
from src.config import get_config
from src.orchestrator.debate import DebateRound, run_debate_round
from src.orchestrator.rounds import convergence_detected
from src.persistence import database as db
from src.signals.schema import Forecast, Signal


@dataclass
class SwarmResult:
    """Result of a full swarm forecast run."""

    run_id: str = ""
    asset: str = ""
    horizon: str = ""
    signals: list[Signal] = field(default_factory=list)
    debate_rounds: list[DebateRound] = field(default_factory=list)
    forecast: Forecast | None = None
    errors: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0


async def _run_single_agent(
    agent: Agent,
    asset: str,
    horizon: str,
    timeout: int,
) -> Signal | str:
    """Run a single agent with timeout. Returns Signal or error string."""
    prompt = (
        f"Analyze {asset} and produce a forecast signal for a {horizon} horizon. "
        f"Use your tools to fetch current data, then emit a structured Signal. "
        f"Set agent_id to '{agent.name}'."
    )
    try:
        result = await asyncio.wait_for(
            Runner.run(agent, input=prompt),
            timeout=timeout,
        )
        signal = result.final_output_as(agent.output_type)
        return signal
    except asyncio.TimeoutError:
        return f"{agent.name}: timed out after {timeout}s"
    except Exception as e:
        return f"{agent.name}: {type(e).__name__}: {e}"


async def _persist_signals(run_id: str, signals: list[Signal], phase: str = "initial") -> None:
    """Save all signals for a run."""
    for s in signals:
        await db.save_signal(
            run_id=run_id,
            agent_id=s.agent_id,
            direction=s.direction,
            magnitude=s.magnitude,
            confidence=s.confidence,
            horizon=s.horizon,
            evidence=[e.model_dump() for e in s.evidence],
            risks=s.risks,
            contrarian_note=s.contrarian_note,
            phase=phase,
        )
        await db.save_calibration_entry(
            run_id=run_id,
            agent_id=s.agent_id,
            asset=s.asset,
            predicted_direction=s.direction,
            predicted_confidence=s.confidence,
        )


async def _persist_debate(run_id: str, debate_round: DebateRound) -> None:
    """Save debate challenges and revisions."""
    for c in debate_round.challenges:
        response_type = None
        response_text = None
        for r in debate_round.revisions:
            if r.agent_id == c.target_id:
                if r.revised_signal:
                    response_type = "revision"
                    response_text = r.revision_reason
                elif r.defense:
                    response_type = "defense"
                    response_text = r.defense
                break

        await db.save_debate(
            run_id=run_id,
            round_number=debate_round.round_number,
            challenger_id=c.challenger_id,
            target_id=c.target_id,
            argument=c.argument,
            evidence_gap=c.evidence_gap,
            suggested_revision=c.suggested_revision,
            response_type=response_type,
            response_text=response_text,
        )


async def _persist_forecast(run_id: str, forecast: Forecast) -> None:
    """Save the aggregated forecast."""
    await db.save_forecast(
        run_id=run_id,
        asset=forecast.asset,
        direction=forecast.direction,
        expected_move=forecast.expected_move,
        ci_lower=forecast.confidence_interval[0],
        ci_upper=forecast.confidence_interval[1],
        horizon=forecast.horizon,
        conviction=forecast.conviction,
        consensus_strength=forecast.consensus_strength,
        key_drivers=forecast.key_drivers,
        key_risks=forecast.key_risks,
        dissenting_view=forecast.dissenting_view,
        debate_summary=forecast.debate_summary,
    )


async def run_swarm(
    asset: str,
    horizon: str = "30d",
    agent_ids: list[str] | None = None,
    skip_debate: bool = False,
    skip_aggregation: bool = False,
    persist: bool = True,
) -> SwarmResult:
    """Run the full swarm pipeline: parallel analysis → debate → aggregation.

    Args:
        asset: Asset to forecast (e.g., 'XAUUSD', 'CL1', 'SPX').
        horizon: Forecast horizon (e.g., '7d', '30d', '90d').
        agent_ids: Optional list of specific agents to run.
        skip_debate: Skip debate rounds.
        skip_aggregation: Skip aggregation (signals only).
        persist: Whether to save results to the database.

    Returns:
        SwarmResult with signals, debate transcript, and final forecast.
    """
    config = get_config()
    agents = create_swarm(agent_ids)
    timeout = config.agent_timeout_seconds

    # Initialize DB and create run record
    run_id = ""
    if persist:
        await db.init_db()
        run_id = await db.create_run(asset, horizon, len(agents))

    start = time.monotonic()
    errors: list[str] = []

    # === Phase 1: Independent Analysis (parallel) ===
    results = await asyncio.gather(
        *[_run_single_agent(agent, asset, horizon, timeout) for agent in agents],
        return_exceptions=True,
    )

    signals: list[Signal] = []
    for result in results:
        if isinstance(result, Signal):
            signals.append(result)
        elif isinstance(result, str):
            errors.append(result)
        elif isinstance(result, Exception):
            errors.append(f"Unexpected error: {result}")

    # Persist initial signals
    if persist and signals:
        await _persist_signals(run_id, signals, phase="initial")

    # Need at least 2 signals to debate
    if len(signals) < 2 or skip_debate:
        elapsed = time.monotonic() - start
        if persist:
            await db.complete_run(run_id, "completed", 0, elapsed)
        return SwarmResult(
            run_id=run_id, asset=asset, horizon=horizon,
            signals=signals, errors=errors, elapsed_seconds=round(elapsed, 2),
        )

    # === Phase 2: Adversarial Debate ===
    debate_rounds: list[DebateRound] = []
    current_signals = signals

    for round_num in range(1, config.max_debate_rounds + 1):
        try:
            debate_round = await run_debate_round(
                agents=agents,
                signals=current_signals,
                round_number=round_num,
                timeout=timeout,
            )
            debate_rounds.append(debate_round)

            # Persist debate
            if persist:
                await _persist_debate(run_id, debate_round)
                await _persist_signals(run_id, debate_round.revised_signals, phase=f"debate_r{round_num}")

            if convergence_detected(current_signals, debate_round.revised_signals):
                current_signals = debate_round.revised_signals
                break

            current_signals = debate_round.revised_signals
        except Exception as e:
            errors.append(f"Debate round {round_num} failed: {e}")
            break

    # === Phase 3: Aggregation ===
    forecast: Forecast | None = None

    if not skip_aggregation:
        try:
            aggregator = create_aggregator_agent()
            aggregator_prompt = build_aggregator_prompt(current_signals, debate_rounds)

            agg_result = await asyncio.wait_for(
                Runner.run(aggregator, input=aggregator_prompt),
                timeout=timeout,
            )
            forecast = agg_result.final_output_as(Forecast)

            if persist and forecast:
                await _persist_forecast(run_id, forecast)
        except asyncio.TimeoutError:
            errors.append("Aggregator timed out")
        except Exception as e:
            errors.append(f"Aggregation failed: {e}")

    elapsed = time.monotonic() - start

    if persist:
        status = "completed" if forecast else "partial"
        await db.complete_run(run_id, status, len(debate_rounds), elapsed)

    return SwarmResult(
        run_id=run_id, asset=asset, horizon=horizon,
        signals=current_signals, debate_rounds=debate_rounds,
        forecast=forecast, errors=errors, elapsed_seconds=round(elapsed, 2),
    )
