"""Multi-round convergence logic.

Determines when the debate should stop based on signal stability.
"""

from __future__ import annotations

from src.signals.schema import Signal

# Convergence thresholds
DIRECTION_AGREEMENT_THRESHOLD = 0.75  # 3 of 4 agents must agree on direction
CONFIDENCE_SHIFT_THRESHOLD = 0.1     # Max confidence change to be considered stable


def convergence_detected(
    previous_signals: list[Signal],
    current_signals: list[Signal],
) -> bool:
    """Check if the swarm has converged and debate can stop.

    Convergence requires BOTH:
    1. Direction agreement: ≥75% of agents agree on direction
    2. Confidence stability: no agent shifted confidence >0.1 since last round

    Args:
        previous_signals: Signals from the previous round.
        current_signals: Signals from the current round.

    Returns:
        True if convergence is detected.
    """
    if not current_signals:
        return True

    # Check direction agreement
    directions = [s.direction for s in current_signals]
    direction_counts = {d: directions.count(d) for d in set(directions)}
    max_agreement = max(direction_counts.values())
    agreement_ratio = max_agreement / len(directions)

    if agreement_ratio < DIRECTION_AGREEMENT_THRESHOLD:
        return False

    # Check confidence stability
    prev_conf_map = {s.agent_id: s.confidence for s in previous_signals}
    for signal in current_signals:
        prev_conf = prev_conf_map.get(signal.agent_id)
        if prev_conf is not None:
            shift = abs(signal.confidence - prev_conf)
            if shift > CONFIDENCE_SHIFT_THRESHOLD:
                return False

    return True


def compute_consensus_strength(signals: list[Signal]) -> float:
    """Compute how strongly agents agree (0 = full split, 1 = unanimous).

    Uses both direction agreement and confidence-weighted alignment.

    Args:
        signals: Current agent signals.

    Returns:
        Float from 0.0 to 1.0.
    """
    if not signals:
        return 0.0

    # Direction component (0 to 1)
    directions = [s.direction for s in signals]
    direction_counts = {d: directions.count(d) for d in set(directions)}
    max_agreement = max(direction_counts.values())
    direction_score = (max_agreement / len(directions) - 0.5) * 2  # Scale: 0.5->0, 1.0->1

    # Confidence-weighted direction alignment
    # Map directions to numeric: bullish=+1, bearish=-1, neutral=0
    dir_map = {"bullish": 1.0, "bearish": -1.0, "neutral": 0.0}
    weighted_sum = sum(dir_map[s.direction] * s.confidence for s in signals)
    total_confidence = sum(s.confidence for s in signals)

    if total_confidence > 0:
        alignment = abs(weighted_sum / total_confidence)  # 0 = split, 1 = aligned
    else:
        alignment = 0.0

    # Combine direction agreement and confidence alignment
    consensus = (direction_score * 0.4 + alignment * 0.6)
    return max(0.0, min(1.0, consensus))
