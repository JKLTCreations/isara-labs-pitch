"""Swarm orchestrator — full pipeline: parallel analysis → debate → aggregation."""

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
from src.signals.schema import Forecast, Signal


@dataclass
class SwarmResult:
    """Result of a full swarm forecast run."""

    asset: str
    horizon: str
    signals: list[Signal]
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


async def run_swarm(
    asset: str,
    horizon: str = "30d",
    agent_ids: list[str] | None = None,
    skip_debate: bool = False,
    skip_aggregation: bool = False,
) -> SwarmResult:
    """Run the full swarm pipeline: parallel analysis → debate → aggregation.

    Args:
        asset: Asset to forecast (e.g., 'XAUUSD', 'CL1', 'SPX').
        horizon: Forecast horizon (e.g., '7d', '30d', '90d').
        agent_ids: Optional list of specific agents to run.
        skip_debate: Skip debate rounds (Phase 2 behavior).
        skip_aggregation: Skip aggregation (signals only).

    Returns:
        SwarmResult with signals, debate transcript, and final forecast.
    """
    config = get_config()
    agents = create_swarm(agent_ids)
    timeout = config.agent_timeout_seconds

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

    # Need at least 2 signals to debate
    if len(signals) < 2 or skip_debate:
        elapsed = time.monotonic() - start
        return SwarmResult(
            asset=asset,
            horizon=horizon,
            signals=signals,
            errors=errors,
            elapsed_seconds=round(elapsed, 2),
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

            # Check convergence
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
        except asyncio.TimeoutError:
            errors.append("Aggregator timed out")
        except Exception as e:
            errors.append(f"Aggregation failed: {e}")

    elapsed = time.monotonic() - start

    return SwarmResult(
        asset=asset,
        horizon=horizon,
        signals=current_signals,
        debate_rounds=debate_rounds,
        forecast=forecast,
        errors=errors,
        elapsed_seconds=round(elapsed, 2),
    )
