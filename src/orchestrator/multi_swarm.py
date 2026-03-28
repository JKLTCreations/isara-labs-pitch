"""Multi-swarm orchestrator — parallel swarms for correlated assets.

When forecasting an asset with known correlations (e.g., gold correlates
with USD and treasuries), this module runs parallel swarms for each
correlated asset and then performs cross-swarm analysis.

Key features:
- Parallel execution of independent swarms
- Cross-swarm signal sharing (read-only)
- Correlation-aware conflict detection
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from src.agents.triage import get_correlated_assets, select_agents
from src.logging import get_logger
from src.orchestrator.swarm import SwarmResult, run_swarm

log = get_logger()


@dataclass
class MultiSwarmResult:
    """Result of a multi-swarm run across correlated assets."""

    primary_asset: str
    primary_result: SwarmResult
    correlated_results: dict[str, SwarmResult] = field(default_factory=dict)
    cross_swarm_conflicts: list[str] = field(default_factory=list)
    correlation_notes: list[str] = field(default_factory=list)


def _detect_cross_swarm_conflicts(
    primary: SwarmResult,
    correlated: dict[str, SwarmResult],
) -> tuple[list[str], list[str]]:
    """Detect when correlated asset swarms produce conflicting signals.

    Known correlation relationships:
    - Gold is typically inversely correlated with USD (DXY)
    - Gold and treasuries (TLT) move together in risk-off
    - Oil and USD are inversely correlated
    - SPX and TLT are inversely correlated in normal regimes

    Args:
        primary: The primary asset's swarm result.
        correlated: Results for correlated assets.

    Returns:
        Tuple of (conflicts, notes).
    """
    conflicts: list[str] = []
    notes: list[str] = []

    primary_direction = None
    if primary.forecast:
        primary_direction = primary.forecast.direction
    elif primary.signals:
        # Use majority direction from signals
        dirs = [s.direction for s in primary.signals]
        primary_direction = max(set(dirs), key=dirs.count)

    if not primary_direction:
        return conflicts, notes

    # Inverse correlation pairs
    inverse_pairs: dict[str, list[str]] = {
        "XAUUSD": ["DXY"],
        "gold": ["DXY"],
        "CL1": ["DXY"],
        "oil": ["DXY"],
        "SPX": ["TLT"],
    }

    # Positive correlation pairs
    positive_pairs: dict[str, list[str]] = {
        "XAUUSD": ["TLT"],
        "gold": ["TLT"],
    }

    inverse_assets = inverse_pairs.get(primary.asset, [])
    positive_assets = positive_pairs.get(primary.asset, [])

    for asset, result in correlated.items():
        corr_direction = None
        if result.forecast:
            corr_direction = result.forecast.direction
        elif result.signals:
            dirs = [s.direction for s in result.signals]
            corr_direction = max(set(dirs), key=dirs.count)

        if not corr_direction or corr_direction == "neutral":
            continue

        # Check inverse correlations: same direction = conflict
        if asset in inverse_assets:
            if primary_direction == corr_direction and primary_direction != "neutral":
                conflicts.append(
                    f"Conflict: {primary.asset} and {asset} are both {primary_direction}, "
                    f"but are historically inversely correlated. "
                    f"This suggests one forecast may be wrong or a regime shift is occurring."
                )
            else:
                notes.append(
                    f"{primary.asset} ({primary_direction}) vs {asset} ({corr_direction}) — "
                    f"consistent with inverse correlation."
                )

        # Check positive correlations: opposite direction = conflict
        if asset in positive_assets:
            opposite = {"bullish": "bearish", "bearish": "bullish"}
            if corr_direction == opposite.get(primary_direction):
                conflicts.append(
                    f"Conflict: {primary.asset} is {primary_direction} but {asset} is "
                    f"{corr_direction}. These assets typically move together. "
                    f"This divergence may indicate a structural shift or a weak signal."
                )
            else:
                notes.append(
                    f"{primary.asset} ({primary_direction}) and {asset} ({corr_direction}) — "
                    f"consistent with positive correlation."
                )

    return conflicts, notes


async def run_multi_swarm(
    asset: str,
    horizon: str = "30d",
    context: str | None = None,
    persist: bool = True,
    run_id: str | None = None,
) -> MultiSwarmResult:
    """Run parallel swarms for an asset and its correlated assets.

    1. Determine correlated assets via triage
    2. Run independent swarms in parallel (each with triage-selected agents)
    3. Detect cross-swarm conflicts
    4. Return combined results

    Args:
        asset: Primary asset to forecast.
        horizon: Forecast horizon.
        context: Optional context for triage agent selection.
        persist: Whether to persist results.

    Returns:
        MultiSwarmResult with all swarm results and cross-swarm analysis.
    """
    correlated_assets = get_correlated_assets(asset)

    # Separate primary from correlated
    other_assets = [a for a in correlated_assets if a != asset]

    log.info(
        "multi_swarm_started",
        primary_asset=asset,
        correlated_assets=other_assets,
        total_swarms=1 + len(other_assets),
    )

    # Run all swarms in parallel
    async def _run_single(target_asset: str, existing_run_id: str | None = None) -> tuple[str, SwarmResult]:
        agent_ids = select_agents(target_asset, context)
        result = await run_swarm(
            asset=target_asset,
            horizon=horizon,
            agent_ids=agent_ids,
            persist=persist,
            run_id=existing_run_id,
        )
        return target_asset, result

    # Pass the existing run_id only for the primary asset to avoid duplicate runs
    tasks = [_run_single(asset, existing_run_id=run_id)] + [_run_single(a) for a in other_assets]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Separate primary from correlated results
    primary_result: SwarmResult | None = None
    correlated_results: dict[str, SwarmResult] = {}

    for result in results:
        if isinstance(result, Exception):
            log.error("multi_swarm_error", error=str(result))
            continue
        target_asset, swarm_result = result
        if target_asset == asset:
            primary_result = swarm_result
        else:
            correlated_results[target_asset] = swarm_result

    if primary_result is None:
        log.error("multi_swarm_primary_failed", asset=asset)
        primary_result = SwarmResult(
            asset=asset, horizon=horizon,
            errors=[f"Primary swarm for {asset} failed"],
        )

    # Cross-swarm conflict detection
    conflicts, notes = _detect_cross_swarm_conflicts(primary_result, correlated_results)

    if conflicts:
        log.warning(
            "cross_swarm_conflicts",
            asset=asset,
            conflict_count=len(conflicts),
            conflicts=conflicts,
        )

    log.info(
        "multi_swarm_complete",
        primary_asset=asset,
        correlated_count=len(correlated_results),
        conflict_count=len(conflicts),
    )

    return MultiSwarmResult(
        primary_asset=asset,
        primary_result=primary_result,
        correlated_results=correlated_results,
        cross_swarm_conflicts=conflicts,
        correlation_notes=notes,
    )
