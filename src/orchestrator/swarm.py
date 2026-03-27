"""Swarm orchestrator — full pipeline: parallel analysis -> debate -> aggregation.

All runs, signals, debates, and forecasts are persisted to SQLite.
Includes structured logging, graceful degradation, and token cost tracking.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from agents import Agent, Runner

from src.agents.aggregator import build_aggregator_prompt, create_aggregator_agent
from src.agents.registry import create_swarm
from src.agents.triage import select_agents
from src.config import get_config
from src.logging import get_logger
from src.orchestrator.debate import DebateRound, run_debate_round
from src.orchestrator.rounds import convergence_detected
from src.persistence import database as db
from src.resilience import TokenUsage, validate_asset, validate_horizon
from src.signals.schema import Forecast, Signal

log = get_logger()


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
    token_usage: TokenUsage | None = None
    degraded: bool = False  # True if some agents failed but run continued


async def _run_single_agent(
    agent: Agent,
    asset: str,
    horizon: str,
    timeout: int,
    token_usage: TokenUsage | None = None,
) -> Signal | str:
    """Run a single agent with timeout. Returns Signal or error string."""
    prompt = (
        f"Analyze {asset} and produce a forecast signal for a {horizon} horizon. "
        f"Use your tools to fetch current data, then emit a structured Signal. "
        f"Set agent_id to '{agent.name}'."
    )
    agent_start = time.monotonic()
    try:
        result = await asyncio.wait_for(
            Runner.run(agent, input=prompt),
            timeout=timeout,
        )
        signal = result.final_output_as(agent.output_type)
        elapsed = round(time.monotonic() - agent_start, 2)

        # Track token usage if available
        if token_usage and hasattr(result, "raw_responses"):
            prompt_tokens = sum(
                getattr(r, "usage", None).prompt_tokens
                for r in result.raw_responses
                if getattr(r, "usage", None)
            )
            completion_tokens = sum(
                getattr(r, "usage", None).completion_tokens
                for r in result.raw_responses
                if getattr(r, "usage", None)
            )
            token_usage.record(agent.name, "analysis", prompt_tokens, completion_tokens)

        log.info(
            "agent_complete",
            agent_id=agent.name,
            direction=signal.direction,
            confidence=signal.confidence,
            evidence_count=len(signal.evidence),
            elapsed_seconds=elapsed,
        )
        return signal
    except asyncio.TimeoutError:
        elapsed = round(time.monotonic() - agent_start, 2)
        log.warning(
            "agent_timeout",
            agent_id=agent.name,
            timeout=timeout,
            elapsed_seconds=elapsed,
        )
        return f"{agent.name}: timed out after {timeout}s"
    except Exception as e:
        elapsed = round(time.monotonic() - agent_start, 2)
        log.error(
            "agent_error",
            agent_id=agent.name,
            error=str(e),
            error_type=type(e).__name__,
            elapsed_seconds=elapsed,
        )
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
    context: str | None = None,
    skip_debate: bool = False,
    skip_aggregation: bool = False,
    persist: bool = True,
) -> SwarmResult:
    """Run the full swarm pipeline: parallel analysis -> debate -> aggregation.

    When no agent_ids are provided, the triage system selects the optimal
    swarm composition based on the asset and optional context. This enables
    dynamic agent selection (e.g., energy specialist for oil, china specialist for CNY).

    Graceful degradation: if some agents fail, the swarm continues with
    the remaining signals (minimum 2 required for debate).

    Args:
        asset: Asset to forecast (e.g., 'XAUUSD', 'CL1', 'SPX').
        horizon: Forecast horizon (e.g., '7d', '30d', '90d').
        agent_ids: Optional list of specific agents to run. If None, triage selects.
        context: Optional context string for triage agent selection.
        skip_debate: Skip debate rounds.
        skip_aggregation: Skip aggregation (signals only).
        persist: Whether to save results to the database.

    Returns:
        SwarmResult with signals, debate transcript, and final forecast.
    """
    config = get_config()
    timeout = config.agent_timeout_seconds

    # Input validation
    asset_err = validate_asset(asset)
    if asset_err:
        return SwarmResult(asset=asset, horizon=horizon, errors=[asset_err])

    horizon_err = validate_horizon(horizon)
    if horizon_err:
        return SwarmResult(asset=asset, horizon=horizon, errors=[horizon_err])

    # Triage: select agents dynamically if not explicitly provided
    if agent_ids is None:
        agent_ids = select_agents(asset, context)
        log.info(
            "triage_selected",
            asset=asset,
            context=context,
            selected_agents=agent_ids,
        )

    agents = create_swarm(agent_ids)
    token_usage = TokenUsage(run_id="")

    # Initialize DB and create run record
    run_id = ""
    if persist:
        await db.init_db()
        run_id = await db.create_run(asset, horizon, len(agents))

    token_usage.run_id = run_id
    start = time.monotonic()
    errors: list[str] = []
    degraded = False

    log.info(
        "swarm_started",
        run_id=run_id,
        asset=asset,
        horizon=horizon,
        agent_count=len(agents),
        phase="analysis",
    )

    # === Phase 1: Independent Analysis (parallel) ===
    results = await asyncio.gather(
        *[_run_single_agent(agent, asset, horizon, timeout, token_usage) for agent in agents],
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

    # Graceful degradation: some agents failed but we got enough
    if len(signals) < len(agents):
        degraded = True
        log.warning(
            "swarm_degraded",
            run_id=run_id,
            expected_agents=len(agents),
            actual_signals=len(signals),
            failed_agents=len(agents) - len(signals),
            phase="analysis",
        )

    # Persist initial signals
    if persist and signals:
        await _persist_signals(run_id, signals, phase="initial")

    log.info(
        "analysis_complete",
        run_id=run_id,
        signal_count=len(signals),
        error_count=len(errors),
        phase="analysis",
    )

    # Need at least 2 signals to debate
    if len(signals) < 2 or skip_debate:
        elapsed = time.monotonic() - start
        if persist:
            status = "completed" if signals else "failed"
            await db.complete_run(run_id, status, 0, elapsed)
        return SwarmResult(
            run_id=run_id, asset=asset, horizon=horizon,
            signals=signals, errors=errors, elapsed_seconds=round(elapsed, 2),
            token_usage=token_usage, degraded=degraded,
        )

    # === Phase 2: Adversarial Debate ===
    debate_rounds: list[DebateRound] = []
    current_signals = signals

    log.info("debate_started", run_id=run_id, max_rounds=config.max_debate_rounds, phase="debate")

    for round_num in range(1, config.max_debate_rounds + 1):
        try:
            debate_round = await run_debate_round(
                agents=agents,
                signals=current_signals,
                round_number=round_num,
                timeout=timeout,
            )
            debate_rounds.append(debate_round)

            log.info(
                "debate_round_complete",
                run_id=run_id,
                round=round_num,
                challenges=len(debate_round.challenges),
                revisions=len(debate_round.revisions),
                phase="debate",
            )

            # Persist debate
            if persist:
                await _persist_debate(run_id, debate_round)
                await _persist_signals(run_id, debate_round.revised_signals, phase=f"debate_r{round_num}")

            if convergence_detected(current_signals, debate_round.revised_signals):
                log.info("convergence_detected", run_id=run_id, round=round_num, phase="debate")
                current_signals = debate_round.revised_signals
                break

            current_signals = debate_round.revised_signals
        except Exception as e:
            log.error(
                "debate_round_failed",
                run_id=run_id,
                round=round_num,
                error=str(e),
                phase="debate",
            )
            errors.append(f"Debate round {round_num} failed: {e}")
            # Graceful fallback: skip to aggregation with current signals
            break

    # === Phase 3: Aggregation ===
    forecast: Forecast | None = None

    if not skip_aggregation:
        log.info("aggregation_started", run_id=run_id, signal_count=len(current_signals), phase="aggregation")
        try:
            aggregator = create_aggregator_agent()
            aggregator_prompt = build_aggregator_prompt(current_signals, debate_rounds)

            agg_result = await asyncio.wait_for(
                Runner.run(aggregator, input=aggregator_prompt),
                timeout=timeout,
            )
            forecast = agg_result.final_output_as(Forecast)

            # Track aggregator tokens
            if hasattr(agg_result, "raw_responses"):
                prompt_tokens = sum(
                    getattr(r, "usage", None).prompt_tokens
                    for r in agg_result.raw_responses
                    if getattr(r, "usage", None)
                )
                completion_tokens = sum(
                    getattr(r, "usage", None).completion_tokens
                    for r in agg_result.raw_responses
                    if getattr(r, "usage", None)
                )
                token_usage.record("aggregator", "aggregation", prompt_tokens, completion_tokens)

            if persist and forecast:
                await _persist_forecast(run_id, forecast)

            log.info(
                "aggregation_complete",
                run_id=run_id,
                direction=forecast.direction,
                conviction=forecast.conviction,
                consensus_strength=forecast.consensus_strength,
                phase="aggregation",
            )
        except asyncio.TimeoutError:
            log.error("aggregator_timeout", run_id=run_id, timeout=timeout, phase="aggregation")
            errors.append("Aggregator timed out")
        except Exception as e:
            log.error(
                "aggregation_failed",
                run_id=run_id,
                error=str(e),
                phase="aggregation",
            )
            errors.append(f"Aggregation failed: {e}")

    elapsed = time.monotonic() - start

    if persist:
        status = "completed" if forecast else "partial"
        await db.complete_run(run_id, status, len(debate_rounds), elapsed)

    # Cost tracking
    cost = token_usage.estimated_cost_usd
    if cost > config.max_cost_per_run_usd:
        log.warning(
            "cost_threshold_exceeded",
            run_id=run_id,
            cost_usd=round(cost, 4),
            threshold_usd=config.max_cost_per_run_usd,
            total_tokens=token_usage.total_tokens,
        )

    log.info(
        "swarm_complete",
        run_id=run_id,
        asset=asset,
        horizon=horizon,
        status="completed" if forecast else "partial",
        signal_count=len(current_signals),
        debate_rounds=len(debate_rounds),
        error_count=len(errors),
        elapsed_seconds=round(elapsed, 2),
        total_tokens=token_usage.total_tokens,
        estimated_cost_usd=round(cost, 4),
        degraded=degraded,
    )

    return SwarmResult(
        run_id=run_id, asset=asset, horizon=horizon,
        signals=current_signals, debate_rounds=debate_rounds,
        forecast=forecast, errors=errors, elapsed_seconds=round(elapsed, 2),
        token_usage=token_usage, degraded=degraded,
    )
