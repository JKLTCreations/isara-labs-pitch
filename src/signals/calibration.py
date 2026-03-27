"""Confidence calibration tracking.

Tracks whether agent confidence scores are well-calibrated:
an agent saying 0.8 confidence should be correct ~80% of the time.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.persistence.database import get_agent_calibration


@dataclass
class CalibrationProfile:
    """An agent's calibration profile."""

    agent_id: str
    total_predictions: int
    overall_accuracy: float | None
    calibration_weight: float  # 0-1, higher = better calibrated
    buckets: dict[str, dict]


async def get_calibration_profile(agent_id: str, asset: str | None = None) -> CalibrationProfile:
    """Get calibration profile for an agent.

    Args:
        agent_id: The agent to profile.
        asset: Optionally filter to a specific asset.

    Returns:
        CalibrationProfile with accuracy and calibration weight.
    """
    stats = await get_agent_calibration(agent_id, asset)

    if stats["total"] == 0 or stats["accuracy"] is None:
        return CalibrationProfile(
            agent_id=agent_id,
            total_predictions=0,
            overall_accuracy=None,
            calibration_weight=1.0,  # Default weight when no history
            buckets={},
        )

    # Compute calibration weight from bucket-level accuracy
    # Perfect calibration = actual accuracy matches predicted confidence in each bucket
    buckets = stats.get("calibration_by_bucket", {})
    if buckets:
        errors = []
        for bucket_label, bucket_data in buckets.items():
            # Parse bucket midpoint (e.g., "60-70%" -> 0.65)
            try:
                low = int(bucket_label.split("-")[0]) / 100
                mid = low + 0.05
            except (ValueError, IndexError):
                mid = 0.5
            actual = bucket_data["actual_accuracy"]
            errors.append(abs(mid - actual))

        avg_error = sum(errors) / len(errors) if errors else 0
        # Weight: 1.0 = perfectly calibrated, 0.0 = maximally miscalibrated
        calibration_weight = max(0.0, 1.0 - avg_error * 2)
    else:
        calibration_weight = 1.0

    return CalibrationProfile(
        agent_id=agent_id,
        total_predictions=stats["total"],
        overall_accuracy=stats["accuracy"],
        calibration_weight=round(calibration_weight, 3),
        buckets=buckets,
    )


async def get_swarm_calibration_weights(
    agent_ids: list[str],
    asset: str | None = None,
) -> dict[str, float]:
    """Get calibration weights for all agents in the swarm.

    Returns:
        Dict mapping agent_id -> calibration_weight (0-1).
    """
    weights = {}
    for agent_id in agent_ids:
        profile = await get_calibration_profile(agent_id, asset)
        weights[agent_id] = profile.calibration_weight
    return weights
