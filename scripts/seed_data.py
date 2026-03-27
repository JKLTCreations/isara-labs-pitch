"""Seed the database with sample forecast runs for development.

Usage:
    python scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime, timedelta

from src.persistence.database import (
    init_db,
    create_run,
    complete_run,
    save_signal,
    save_debate,
    save_forecast,
    save_calibration_entry,
    score_calibration,
)


SAMPLE_AGENTS = ["geopolitical_analyst", "macro_economist", "sentiment_analyst", "quant_analyst"]
SAMPLE_ASSETS = ["XAUUSD", "CL1", "SPX"]
DIRECTIONS = ["bullish", "bearish", "neutral"]


def _random_evidence() -> list[dict]:
    sources = [
        ("yfinance:GC=F", "Gold trading at elevated levels near resistance"),
        ("FRED:DGS10", "10Y yield rising, tightening financial conditions"),
        ("news:reuters", "OPEC signaling potential production cut"),
        ("sentiment:vix", "VIX elevated above 20, fear in the market"),
        ("yfinance:DX-Y.NYB", "Dollar index strengthening against majors"),
    ]
    chosen = random.sample(sources, k=random.randint(1, 3))
    return [
        {"source": s, "observation": o, "relevance": round(random.uniform(0.5, 1.0), 2),
         "timestamp": datetime.now().isoformat()}
        for s, o in chosen
    ]


async def seed() -> None:
    await init_db()
    print("Seeding database with sample forecast runs...\n")

    for i in range(5):
        asset = random.choice(SAMPLE_ASSETS)
        horizon = random.choice(["7d", "30d", "90d"])
        base_date = datetime.now() - timedelta(days=30 * (5 - i))

        run_id = await create_run(asset, horizon, len(SAMPLE_AGENTS))

        # Signals
        majority_dir = random.choice(["bullish", "bearish"])
        for agent_id in SAMPLE_AGENTS:
            direction = majority_dir if random.random() > 0.3 else random.choice(DIRECTIONS)
            confidence = round(random.uniform(0.4, 0.9), 2)
            magnitude = round(random.uniform(-0.1, 0.1), 3)
            if direction == "bearish":
                magnitude = -abs(magnitude)
            elif direction == "bullish":
                magnitude = abs(magnitude)

            await save_signal(
                run_id=run_id, agent_id=agent_id, direction=direction,
                magnitude=magnitude, confidence=confidence, horizon=horizon,
                evidence=_random_evidence(), risks=["Market volatility", "Policy surprise"],
                phase="initial",
            )
            await save_calibration_entry(
                run_id=run_id, agent_id=agent_id, asset=asset,
                predicted_direction=direction, predicted_confidence=confidence,
            )

        # Debate
        challenger = random.choice(SAMPLE_AGENTS)
        target = random.choice([a for a in SAMPLE_AGENTS if a != challenger])
        await save_debate(
            run_id=run_id, round_number=1,
            challenger_id=challenger, target_id=target,
            argument=f"Your analysis ignores the recent shift in macro conditions",
            evidence_gap="Missing FRED rate data from last week",
            suggested_revision="Lower confidence to reflect uncertainty",
            response_type="defense",
            response_text="My technical signals remain strong despite macro headwinds",
        )

        # Forecast
        await save_forecast(
            run_id=run_id, asset=asset, direction=majority_dir,
            expected_move=round(random.uniform(-0.05, 0.05), 4),
            ci_lower=round(random.uniform(-0.1, -0.02), 4),
            ci_upper=round(random.uniform(0.02, 0.1), 4),
            horizon=horizon, conviction=random.choice(["low", "medium", "high"]),
            consensus_strength=round(random.uniform(0.3, 0.9), 2),
            key_drivers=["Rate expectations shifting", "Geopolitical risk elevated"],
            key_risks=["Surprise policy change", "Black swan event"],
            dissenting_view=f"{target} argues opposite direction based on sentiment",
            debate_summary="Agents disagreed on the weight of macro vs technical signals.",
        )

        # Score with fake actual outcome
        actual_dir = random.choice(DIRECTIONS)
        actual_move = round(random.uniform(-0.08, 0.08), 4)
        await score_calibration(run_id, actual_dir, actual_move)

        await complete_run(run_id, "completed", 1, round(random.uniform(20, 90), 2))

        print(f"  Run {run_id}: {asset} {horizon} → {majority_dir} (actual: {actual_dir})")

    print(f"\nSeeded 5 runs. Database at: data/forecasts.db")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
