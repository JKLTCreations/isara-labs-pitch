"""CLI entrypoint: run a single forecast with the quant agent.

Usage:
    python scripts/run_forecast.py --asset XAUUSD --horizon 30d
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from agents import Runner

from src.agents.quant import create_quant_agent
from src.config import get_config


async def run(asset: str, horizon: str, verbose: bool = False) -> None:
    config = get_config()
    errors = config.validate()
    if errors:
        print(f"Config errors: {', '.join(errors)}", file=sys.stderr)
        sys.exit(1)

    agent = create_quant_agent()

    prompt = (
        f"Analyze {asset} and produce a forecast signal for a {horizon} horizon. "
        f"Use your tools to fetch current price data and technical indicators, "
        f"then emit a structured Signal."
    )

    if verbose:
        print(f"Running quant agent on {asset} ({horizon})...\n")

    result = await Runner.run(agent, input=prompt)
    signal = result.final_output_as(agent.output_type)

    if verbose:
        print("=== SIGNAL ===")

    print(json.dumps(signal.model_dump(), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a swarm forecast")
    parser.add_argument("--asset", required=True, help="Asset to forecast (e.g. XAUUSD, CL1, SPX)")
    parser.add_argument("--horizon", default="30d", help="Forecast horizon (e.g. 7d, 30d, 90d)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    asyncio.run(run(args.asset, args.horizon, args.verbose))


if __name__ == "__main__":
    main()
