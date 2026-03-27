"""Agent memory store — per-agent track record and performance history.

Each agent accumulates a history of predictions linked to outcomes.
This history is used to:
1. Generate "track record summary" text injected into agent system prompts
2. Compute adaptive calibration weights
3. Surface domain strengths/weaknesses per agent
"""

from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from src.persistence.database import DB_PATH


@dataclass
class AgentTrackRecord:
    """Summary of an agent's historical performance."""

    agent_id: str
    asset: str | None  # None = across all assets
    total_forecasts: int
    directional_accuracy: float | None
    avg_confidence: float | None
    overconfidence_ratio: float | None  # How often high-conf predictions were wrong
    asset_accuracy: dict[str, float]  # per-asset accuracy breakdown
    recent_streak: str | None  # "3 correct", "2 incorrect", etc.


async def get_agent_track_record(
    agent_id: str,
    asset: str | None = None,
    limit: int = 50,
) -> AgentTrackRecord:
    """Build a track record summary for an agent.

    Args:
        agent_id: Agent to profile.
        asset: Optionally filter to a specific asset.
        limit: Max predictions to consider.

    Returns:
        AgentTrackRecord with accuracy stats.
    """
    async with aiosqlite.connect(str(DB_PATH)) as db:
        # Get scored predictions
        if asset:
            rows = await db.execute_fetchall(
                """SELECT asset, predicted_direction, predicted_confidence, actual_direction, correct
                FROM calibration_log
                WHERE agent_id=? AND asset=? AND correct IS NOT NULL
                ORDER BY scored_at DESC LIMIT ?""",
                (agent_id, asset, limit),
            )
        else:
            rows = await db.execute_fetchall(
                """SELECT asset, predicted_direction, predicted_confidence, actual_direction, correct
                FROM calibration_log
                WHERE agent_id=? AND correct IS NOT NULL
                ORDER BY scored_at DESC LIMIT ?""",
                (agent_id, limit),
            )

    if not rows:
        return AgentTrackRecord(
            agent_id=agent_id,
            asset=asset,
            total_forecasts=0,
            directional_accuracy=None,
            avg_confidence=None,
            overconfidence_ratio=None,
            asset_accuracy={},
            recent_streak=None,
        )

    total = len(rows)
    correct_count = sum(1 for r in rows if r[4] == 1)
    accuracy = correct_count / total

    # Average confidence
    confidences = [r[2] for r in rows]
    avg_conf = sum(confidences) / len(confidences)

    # Overconfidence: high-confidence (>0.7) predictions that were wrong
    high_conf = [(r[2], r[4]) for r in rows if r[2] > 0.7]
    if high_conf:
        high_conf_wrong = sum(1 for _, c in high_conf if c == 0)
        overconfidence = high_conf_wrong / len(high_conf)
    else:
        overconfidence = None

    # Per-asset accuracy
    asset_groups: dict[str, list[int]] = {}
    for r in rows:
        a = r[0]
        asset_groups.setdefault(a, []).append(r[4])

    asset_acc = {}
    for a, outcomes in asset_groups.items():
        if outcomes:
            asset_acc[a] = round(sum(outcomes) / len(outcomes), 3)

    # Recent streak
    streak_count = 0
    streak_type = None
    for r in rows:
        c = r[4]
        if streak_type is None:
            streak_type = "correct" if c == 1 else "incorrect"
            streak_count = 1
        elif (c == 1 and streak_type == "correct") or (c == 0 and streak_type == "incorrect"):
            streak_count += 1
        else:
            break

    streak = f"{streak_count} {streak_type}" if streak_type else None

    return AgentTrackRecord(
        agent_id=agent_id,
        asset=asset,
        total_forecasts=total,
        directional_accuracy=round(accuracy, 3),
        avg_confidence=round(avg_conf, 3),
        overconfidence_ratio=round(overconfidence, 3) if overconfidence is not None else None,
        asset_accuracy=asset_acc,
        recent_streak=streak,
    )


def format_track_record_prompt(record: AgentTrackRecord) -> str:
    """Format a track record into text for injection into agent system prompts.

    Args:
        record: Agent's track record.

    Returns:
        Human-readable performance summary, or empty string if no history.
    """
    if record.total_forecasts == 0:
        return ""

    asset_label = record.asset or "all assets"
    lines = [
        f"\n=== YOUR TRACK RECORD ({asset_label}, last {record.total_forecasts} forecasts) ===",
    ]

    if record.directional_accuracy is not None:
        pct = round(record.directional_accuracy * 100, 1)
        lines.append(f"- Directional accuracy: {pct}%")

    if record.avg_confidence is not None:
        lines.append(f"- Your average confidence: {record.avg_confidence:.2f}")

    if record.overconfidence_ratio is not None:
        pct = round(record.overconfidence_ratio * 100, 1)
        if record.overconfidence_ratio > 0.3:
            lines.append(
                f"- WARNING: When you say confidence >0.7, you are WRONG {pct}% of the time. "
                f"Consider lowering your confidence scores."
            )
        elif record.overconfidence_ratio < 0.1:
            lines.append(
                f"- Your high-confidence calls are well-calibrated ({pct}% error rate)."
            )

    if record.asset_accuracy and len(record.asset_accuracy) > 1:
        best = max(record.asset_accuracy.items(), key=lambda x: x[1])
        worst = min(record.asset_accuracy.items(), key=lambda x: x[1])
        if best[1] != worst[1]:
            lines.append(
                f"- Best asset: {best[0]} ({round(best[1]*100,1)}% accuracy), "
                f"Worst: {worst[0]} ({round(worst[1]*100,1)}% accuracy)"
            )

    if record.recent_streak:
        lines.append(f"- Recent streak: {record.recent_streak}")

    lines.append(
        "Use this track record to calibrate your confidence. "
        "If you've been overconfident, lower your scores. "
        "If you've been accurate, maintain your approach."
    )

    return "\n".join(lines)


async def get_all_agent_track_records(
    agent_ids: list[str],
    asset: str | None = None,
) -> dict[str, AgentTrackRecord]:
    """Get track records for all agents in a swarm.

    Args:
        agent_ids: Agent identifiers.
        asset: Optionally filter to a specific asset.

    Returns:
        Dict mapping agent_id -> AgentTrackRecord.
    """
    records = {}
    for agent_id in agent_ids:
        records[agent_id] = await get_agent_track_record(agent_id, asset)
    return records
