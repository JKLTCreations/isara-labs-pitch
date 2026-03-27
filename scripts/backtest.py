"""Backtesting harness — run historical forecasts and score accuracy.

Usage:
    python scripts/backtest.py --asset XAUUSD --start 2025-01-01 --end 2025-10-01 --interval monthly
    python scripts/backtest.py --asset XAUUSD --start 2025-06-01 --end 2025-12-01 --interval monthly -v
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta

import yfinance as yf

from src.config import get_config
from src.mcp.market_server import ASSET_TICKER_MAP
from src.orchestrator.swarm import run_swarm
from src.persistence.database import init_db, score_calibration, get_agent_calibration


def _generate_dates(start: str, end: str, interval: str) -> list[datetime]:
    """Generate backtest dates."""
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    dates = []

    current = start_dt
    while current <= end_dt:
        dates.append(current)
        if interval == "weekly":
            current += timedelta(days=7)
        elif interval == "monthly":
            month = current.month + 1
            year = current.year
            if month > 12:
                month = 1
                year += 1
            current = current.replace(year=year, month=month)
        elif interval == "quarterly":
            month = current.month + 3
            year = current.year
            while month > 12:
                month -= 12
                year += 1
            current = current.replace(year=year, month=month)
        else:
            current += timedelta(days=int(interval.rstrip("d")))

    return dates


def _get_actual_move(asset: str, forecast_date: datetime, horizon_days: int) -> tuple[str, float] | None:
    """Get what actually happened after the forecast date."""
    ticker_symbol = ASSET_TICKER_MAP.get(asset, asset)
    ticker = yf.Ticker(ticker_symbol)

    # Fetch data around the forecast date
    start = forecast_date - timedelta(days=5)
    end = forecast_date + timedelta(days=horizon_days + 5)
    hist = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

    if hist.empty or len(hist) < 2:
        return None

    # Find the closest price to forecast date and to horizon end
    forecast_idx = hist.index.searchsorted(forecast_date)
    if forecast_idx >= len(hist):
        forecast_idx = len(hist) - 1

    end_date = forecast_date + timedelta(days=horizon_days)
    end_idx = hist.index.searchsorted(end_date)
    if end_idx >= len(hist):
        end_idx = len(hist) - 1

    if forecast_idx == end_idx:
        return None

    start_price = float(hist["Close"].iloc[forecast_idx])
    end_price = float(hist["Close"].iloc[end_idx])
    pct_move = (end_price - start_price) / start_price

    if pct_move > 0.005:
        direction = "bullish"
    elif pct_move < -0.005:
        direction = "bearish"
    else:
        direction = "neutral"

    return direction, pct_move


async def run_backtest(
    asset: str,
    start: str,
    end: str,
    interval: str = "monthly",
    horizon: str = "30d",
    verbose: bool = False,
) -> None:
    config = get_config()
    errors = config.validate()
    if errors:
        print(f"Config errors: {', '.join(errors)}", file=sys.stderr)
        sys.exit(1)

    await init_db()
    dates = _generate_dates(start, end, interval)
    horizon_days = int(horizon.rstrip("d"))

    print(f"Backtest: {asset} | {start} → {end} | {interval} | {horizon} horizon")
    print(f"Running {len(dates)} forecast simulations...\n")

    results = []

    for i, date in enumerate(dates):
        if verbose:
            print(f"[{i + 1}/{len(dates)}] Forecasting from {date.strftime('%Y-%m-%d')}...", end=" ")

        try:
            swarm_result = await run_swarm(
                asset=asset,
                horizon=horizon,
                persist=True,
            )

            if swarm_result.forecast:
                # Get actual outcome
                actual = _get_actual_move(asset, date, horizon_days)

                entry = {
                    "date": date.strftime("%Y-%m-%d"),
                    "run_id": swarm_result.run_id,
                    "predicted_direction": swarm_result.forecast.direction,
                    "predicted_move": swarm_result.forecast.expected_move,
                    "conviction": swarm_result.forecast.conviction,
                    "consensus": swarm_result.forecast.consensus_strength,
                    "actual_direction": actual[0] if actual else None,
                    "actual_move": round(actual[1], 4) if actual else None,
                    "correct": (
                        swarm_result.forecast.direction == actual[0]
                        if actual else None
                    ),
                    "agent_signals": [
                        {"agent": s.agent_id, "direction": s.direction, "confidence": s.confidence}
                        for s in swarm_result.signals
                    ],
                }
                results.append(entry)

                # Score calibration
                if actual and swarm_result.run_id:
                    await score_calibration(swarm_result.run_id, actual[0], actual[1])

                if verbose:
                    status = "CORRECT" if entry["correct"] else "WRONG" if entry["correct"] is not None else "N/A"
                    print(f"{swarm_result.forecast.direction} (conv={swarm_result.forecast.conviction}) → {status}")
            else:
                if verbose:
                    print("FAILED (no forecast)")
                results.append({"date": date.strftime("%Y-%m-%d"), "error": "no forecast"})

        except Exception as e:
            if verbose:
                print(f"ERROR: {e}")
            results.append({"date": date.strftime("%Y-%m-%d"), "error": str(e)})

    # === Scorecard ===
    scored = [r for r in results if r.get("correct") is not None]
    correct = sum(1 for r in scored if r["correct"])
    total = len(scored)

    print("\n" + "=" * 60)
    print("BACKTEST SCORECARD")
    print("=" * 60)
    print(f"Asset: {asset}")
    print(f"Period: {start} → {end} ({interval})")
    print(f"Horizon: {horizon}")
    print(f"Total runs: {len(results)}")
    print(f"Scored runs: {total}")

    if total > 0:
        print(f"\nDirectional Accuracy: {correct}/{total} ({correct / total * 100:.0f}%)")

        # Brier score (for directional accuracy with confidence)
        brier_scores = []
        for r in scored:
            forecast_prob = r.get("consensus", 0.5)
            outcome = 1.0 if r["correct"] else 0.0
            brier_scores.append((forecast_prob - outcome) ** 2)
        brier = sum(brier_scores) / len(brier_scores)
        print(f"Brier Score: {brier:.3f} (lower is better, 0.25 = random)")

        # Per-agent breakdown
        print("\nPer-Agent Accuracy:")
        agent_results: dict[str, list[bool]] = {}
        for r in scored:
            actual_dir = r["actual_direction"]
            for sig in r.get("agent_signals", []):
                agent_id = sig["agent"]
                agent_results.setdefault(agent_id, []).append(sig["direction"] == actual_dir)

        for agent_id, outcomes in sorted(agent_results.items()):
            acc = sum(outcomes) / len(outcomes)
            print(f"  {agent_id}: {sum(outcomes)}/{len(outcomes)} ({acc * 100:.0f}%)")

        # Conviction breakdown
        print("\nBy Conviction Level:")
        for conv in ["high", "medium", "low"]:
            conv_runs = [r for r in scored if r.get("conviction") == conv]
            if conv_runs:
                conv_correct = sum(1 for r in conv_runs if r["correct"])
                print(f"  {conv}: {conv_correct}/{len(conv_runs)} ({conv_correct / len(conv_runs) * 100:.0f}%)")

    print("=" * 60)

    # Dump full results
    if verbose:
        print("\nFull results:")
        print(json.dumps(results, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest the swarm forecaster")
    parser.add_argument("--asset", required=True, help="Asset to backtest")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--interval", default="monthly", help="Interval: weekly, monthly, quarterly")
    parser.add_argument("--horizon", default="30d", help="Forecast horizon (e.g. 7d, 30d)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    asyncio.run(run_backtest(args.asset, args.start, args.end, args.interval, args.horizon, args.verbose))


if __name__ == "__main__":
    main()
