"""Swarm orchestrator — runs specialist agents in parallel and collects signals.

Phase 2: Parallel independent analysis (no debate yet).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from agents import Agent, Runner

from src.agents.registry import create_swarm
from src.config import get_config
from src.signals.schema import Signal


@dataclass
class SwarmResult:
    """Result of a swarm forecast run."""

    asset: str
    horizon: str
    signals: list[Signal]
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
) -> SwarmResult:
    """Run the specialist swarm on an asset and collect signals.

    All agents run in parallel with no cross-talk (Phase 2).

    Args:
        asset: Asset to forecast (e.g., 'XAUUSD', 'CL1', 'SPX').
        horizon: Forecast horizon (e.g., '7d', '30d', '90d').
        agent_ids: Optional list of specific agents to run.

    Returns:
        SwarmResult with collected signals and any errors.
    """
    config = get_config()
    agents = create_swarm(agent_ids)
    timeout = config.agent_timeout_seconds

    start = time.monotonic()

    # Run all agents in parallel
    results = await asyncio.gather(
        *[_run_single_agent(agent, asset, horizon, timeout) for agent in agents],
        return_exceptions=True,
    )

    signals: list[Signal] = []
    errors: list[str] = []

    for result in results:
        if isinstance(result, Signal):
            signals.append(result)
        elif isinstance(result, str):
            errors.append(result)
        elif isinstance(result, Exception):
            errors.append(f"Unexpected error: {result}")

    elapsed = time.monotonic() - start

    return SwarmResult(
        asset=asset,
        horizon=horizon,
        signals=signals,
        errors=errors,
        elapsed_seconds=round(elapsed, 2),
    )
