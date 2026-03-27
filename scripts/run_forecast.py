"""CLI entrypoint: run the full agent swarm pipeline.

Usage:
    python scripts/run_forecast.py --asset XAUUSD --horizon 30d
    python scripts/run_forecast.py --asset XAUUSD --horizon 30d --no-debate
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
    skip_debate: bool = False,
    verbose: bool = False,
) -> None:
    config = get_config()
    errors = config.validate()
    if errors:
        print(f"Config errors: {', '.join(errors)}", file=sys.stderr)
        sys.exit(1)

    if verbose:
        agents_label = ", ".join(agent_ids) if agent_ids else "full swarm"
        print(f"Running swarm on {asset} ({horizon}) with [{agents_label}]...")
        if skip_debate:
            print("Debate: SKIPPED")
        print()

    result = await run_swarm(
        asset=asset,
        horizon=horizon,
        agent_ids=agent_ids,
        skip_debate=skip_debate,
    )

    # === Signals ===
    if verbose:
        print(f"=== PHASE 1: INDEPENDENT ANALYSIS ({len(result.signals)} signals) ===\n")

    for i, signal in enumerate(result.signals):
        if verbose:
            print(f"--- {signal.agent_id} ({signal.direction}, conf={signal.confidence}) ---")
        print(json.dumps(signal.model_dump(), indent=2))
        if verbose:
            print()

    # === Debate ===
    if result.debate_rounds and verbose:
        print(f"=== PHASE 2: ADVERSARIAL DEBATE ({len(result.debate_rounds)} rounds) ===\n")
        for dr in result.debate_rounds:
            print(f"--- Round {dr.round_number} ---")
            print(f"Challenges: {len(dr.challenges)}")
            for c in dr.challenges:
                print(f"  {c.challenger_id} → {c.target_id}: {c.argument[:120]}...")
            print(f"Revisions: {len(dr.revisions)}")
            for r in dr.revisions:
                if r.revised_signal:
                    reason = r.revision_reason or "no reason given"
                    print(f"  {r.agent_id} REVISED ({r.original_direction} → {r.revised_signal.direction}): {reason[:100]}")
                elif r.defense:
                    print(f"  {r.agent_id} DEFENDED: {r.defense[:100]}")
            print()

    # === Forecast ===
    if result.forecast:
        if verbose:
            print("=== PHASE 3: CONSENSUS FORECAST ===\n")
        print(json.dumps(result.forecast.model_dump(), indent=2))
    elif verbose:
        print("No forecast produced (aggregation skipped or failed).")

    # === Errors ===
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    # === Summary ===
    if verbose:
        print(f"\n=== RUN SUMMARY ===")
        print(f"Asset: {asset} | Horizon: {horizon}")
        print(f"Signals: {len(result.signals)} | Debate rounds: {len(result.debate_rounds)} | Errors: {len(result.errors)}")
        print(f"Elapsed: {result.elapsed_seconds}s")
        if result.forecast:
            f = result.forecast
            print(f"Forecast: {f.direction} | Conviction: {f.conviction} | Consensus: {f.consensus_strength:.2f}")


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
    parser.add_argument("--no-debate", action="store_true", help="Skip adversarial debate")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    asyncio.run(run(args.asset, args.horizon, args.agents, args.no_debate, args.verbose))


if __name__ == "__main__":
    main()
