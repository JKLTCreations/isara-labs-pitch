"""Confidence calibration tracking and adaptive adjustment.

Tracks whether agent confidence scores are well-calibrated:
an agent saying 0.8 confidence should be correct ~80% of the time.

Includes:
- CalibrationProfile: per-agent accuracy and calibration weight
- Platt scaling: logistic regression to map raw confidence -> calibrated confidence
- Adaptive weighting: better-calibrated agents get higher aggregation weight
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from src.persistence.database import get_agent_calibration


@dataclass
class CalibrationProfile:
    """An agent's calibration profile."""

    agent_id: str
    total_predictions: int
    overall_accuracy: float | None
    calibration_weight: float  # 0-1, higher = better calibrated
    buckets: dict[str, dict]
    platt_params: tuple[float, float] | None = None  # (a, b) for sigmoid transform


@dataclass
class PlattScaler:
    """Platt scaling: maps raw confidence to calibrated confidence via sigmoid.

    calibrated = 1 / (1 + exp(a * raw + b))

    Fitted from (predicted_confidence, actual_correct) pairs using
    simple gradient descent.
    """

    a: float = -1.0
    b: float = 0.0

    def transform(self, raw_confidence: float) -> float:
        """Apply Platt scaling to a raw confidence score."""
        z = self.a * raw_confidence + self.b
        # Clamp to avoid overflow
        z = max(-10.0, min(10.0, z))
        calibrated = 1.0 / (1.0 + math.exp(z))
        # Enforce the 0.95 cap
        return min(0.95, max(0.05, calibrated))

    @classmethod
    def fit(cls, predictions: list[tuple[float, int]], lr: float = 0.1, epochs: int = 100) -> PlattScaler:
        """Fit Platt parameters from historical predictions.

        Args:
            predictions: List of (raw_confidence, correct) pairs where correct is 0 or 1.
            lr: Learning rate.
            epochs: Training iterations.

        Returns:
            Fitted PlattScaler.
        """
        if len(predictions) < 5:
            # Not enough data for fitting — return identity-ish transform
            return cls(a=-1.0, b=0.0)

        a = -1.0
        b = 0.0

        for _ in range(epochs):
            da = 0.0
            db = 0.0
            for raw_conf, correct in predictions:
                z = a * raw_conf + b
                z = max(-10.0, min(10.0, z))
                p = 1.0 / (1.0 + math.exp(z))
                error = p - correct
                da += error * raw_conf
                db += error

            n = len(predictions)
            a -= lr * da / n
            b -= lr * db / n

        return cls(a=a, b=b)


async def get_calibration_profile(agent_id: str, asset: str | None = None) -> CalibrationProfile:
    """Get calibration profile for an agent.

    Args:
        agent_id: The agent to profile.
        asset: Optionally filter to a specific asset.

    Returns:
        CalibrationProfile with accuracy, calibration weight, and Platt params.
    """
    stats = await get_agent_calibration(agent_id, asset)

    if stats["total"] == 0 or stats["accuracy"] is None:
        return CalibrationProfile(
            agent_id=agent_id,
            total_predictions=0,
            overall_accuracy=None,
            calibration_weight=1.0,  # Default weight when no history
            buckets={},
            platt_params=None,
        )

    # Compute calibration weight from bucket-level accuracy
    buckets = stats.get("calibration_by_bucket", {})
    if buckets:
        errors = []
        for bucket_label, bucket_data in buckets.items():
            try:
                low = int(bucket_label.split("-")[0]) / 100
                mid = low + 0.05
            except (ValueError, IndexError):
                mid = 0.5
            actual = bucket_data["actual_accuracy"]
            errors.append(abs(mid - actual))

        avg_error = sum(errors) / len(errors) if errors else 0
        calibration_weight = max(0.0, 1.0 - avg_error * 2)
    else:
        calibration_weight = 1.0

    # Fit Platt scaling if enough data
    platt_params = None
    if stats["total"] >= 10:
        predictions = stats.get("raw_predictions", [])
        if predictions:
            scaler = PlattScaler.fit(predictions)
            platt_params = (round(scaler.a, 4), round(scaler.b, 4))

    return CalibrationProfile(
        agent_id=agent_id,
        total_predictions=stats["total"],
        overall_accuracy=stats["accuracy"],
        calibration_weight=round(calibration_weight, 3),
        buckets=buckets,
        platt_params=platt_params,
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


async def calibrate_signal_confidence(
    agent_id: str,
    raw_confidence: float,
    asset: str | None = None,
) -> float:
    """Apply Platt scaling to adjust an agent's raw confidence.

    If no Platt parameters are available (insufficient history),
    returns the raw confidence unchanged.

    Args:
        agent_id: Agent identifier.
        raw_confidence: The agent's self-reported confidence.
        asset: Optionally scope to a specific asset.

    Returns:
        Calibrated confidence value.
    """
    profile = await get_calibration_profile(agent_id, asset)

    if profile.platt_params is None:
        return raw_confidence

    a, b = profile.platt_params
    scaler = PlattScaler(a=a, b=b)
    return scaler.transform(raw_confidence)


def format_calibration_context(
    profiles: dict[str, CalibrationProfile],
) -> str:
    """Format calibration profiles for the aggregator prompt.

    Args:
        profiles: Dict mapping agent_id -> CalibrationProfile.

    Returns:
        Text block describing each agent's calibration for the aggregator.
    """
    if not profiles:
        return ""

    lines = ["\n=== AGENT CALIBRATION PROFILES ===\n"]

    for agent_id, profile in profiles.items():
        if profile.total_predictions == 0:
            lines.append(f"{agent_id}: No track record (default weight)")
            continue

        acc = f"{profile.overall_accuracy*100:.1f}%" if profile.overall_accuracy is not None else "N/A"
        lines.append(
            f"{agent_id}: {profile.total_predictions} predictions, "
            f"accuracy={acc}, "
            f"calibration_weight={profile.calibration_weight:.2f}"
        )

        if profile.platt_params:
            lines.append(
                f"  Platt scaling active: raw confidence is being adjusted"
            )

        # Bucket details
        for bucket, data in profile.buckets.items():
            actual = data["actual_accuracy"]
            count = data["count"]
            lines.append(f"  {bucket}: {actual*100:.0f}% actual accuracy ({count} predictions)")

    lines.append(
        "\nWeight agents with higher calibration_weight more heavily. "
        "Agents with low calibration_weight are systematically overconfident or underconfident."
    )

    return "\n".join(lines)
