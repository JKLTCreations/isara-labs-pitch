"""CLI entrypoint: run the agent swarm on a forecast target.

Usage:
    python scripts/run_forecast.py --asset XAUUSD --horizon 30d
    python scripts/run_forecast.py --asset XAUUSD --horizon 30d --agents quant_analyst macro_economist
    python scripts/run_forecast.py --asset CL1 --horizon 7d -v
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from src.agents.registry import list_agents
from src.config import get_config
from src.orchestrator.swarm import run_swarm


async def run(
    asset: str,
    horizon: str,
    agent_ids: list[str] | None = None,
    verbose: bool = False,
) -> None:
    config = get_config()
    errors = config.validate()
    if errors:
        print(f"Config errors: {', '.join(errors)}", file=sys.stderr)
        sys.exit(1)

    if verbose:
        agents_label = ", ".join(agent_ids) if agent_ids else "full swarm"
        print(f"Running swarm on {asset} ({horizon}) with [{agents_label}]...\n")

    result = await run_swarm(asset=asset, horizon=horizon, agent_ids=agent_ids)

    if verbose:
        print(f"Completed in {result.elapsed_seconds}s")
        print(f"Signals: {len(result.signals)} | Errors: {len(result.errors)}\n")

    # Print each signal
    for i, signal in enumerate(result.signals):
        if verbose:
            print(f"=== SIGNAL {i + 1}: {signal.agent_id} ({signal.direction}, conf={signal.confidence}) ===")
        print(json.dumps(signal.model_dump(), indent=2))
        if verbose:
            print()

    # Print errors
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    # Summary
    if verbose and result.signals:
        directions = [s.direction for s in result.signals]
        print("\n=== SWARM SUMMARY ===")
        print(f"Asset: {asset} | Horizon: {horizon}")
        print(f"Bullish: {directions.count('bullish')} | Bearish: {directions.count('bearish')} | Neutral: {directions.count('neutral')}")
        avg_conf = sum(s.confidence for s in result.signals) / len(result.signals)
        print(f"Average confidence: {avg_conf:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the agent swarm forecaster")
    parser.add_argument("--asset", required=True, help="Asset to forecast (e.g. XAUUSD, CL1, SPX)")
    parser.add_argument("--horizon", default="30d", help="Forecast horizon (e.g. 7d, 30d, 90d)")
    parser.add_argument(
        "--agents",
        nargs="+",
        default=None,
        help=f"Specific agents to run. Available: {list_agents()}",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    asyncio.run(run(args.asset, args.horizon, args.agents, args.verbose))


if __name__ == "__main__":
    main()
