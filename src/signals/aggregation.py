"""Confidence-weighted signal aggregation.

Combines multiple agent signals into a single consensus view
with uncertainty quantification.
"""

from __future__ import annotations

from src.orchestrator.rounds import compute_consensus_strength
from src.signals.schema import Signal


def aggregate_direction(signals: list[Signal]) -> tuple[str, float]:
    """Compute confidence-weighted directional consensus.

    Args:
        signals: Agent signals to aggregate.

    Returns:
        Tuple of (direction, weighted_magnitude).
    """
    dir_map = {"bullish": 1.0, "bearish": -1.0, "neutral": 0.0}
    total_weight = sum(s.confidence for s in signals)

    if total_weight == 0:
        return "neutral", 0.0

    weighted_direction = sum(dir_map[s.direction] * s.confidence for s in signals) / total_weight
    weighted_magnitude = sum(s.magnitude * s.confidence for s in signals) / total_weight

    if weighted_direction > 0.2:
        direction = "bullish"
    elif weighted_direction < -0.2:
        direction = "bearish"
    else:
        direction = "neutral"

    return direction, weighted_magnitude


def compute_confidence_interval(signals: list[Signal]) -> tuple[float, float]:
    """Compute an 80% confidence interval from signal magnitudes.

    Uses the spread of agent estimates as a proxy for uncertainty.

    Args:
        signals: Agent signals.

    Returns:
        Tuple of (lower_bound, upper_bound) as expected % moves.
    """
    if not signals:
        return (0.0, 0.0)

    magnitudes = [s.magnitude for s in signals]
    avg = sum(magnitudes) / len(magnitudes)

    if len(magnitudes) == 1:
        # Single agent — use confidence to scale interval
        half_width = magnitudes[0] * (1 - signals[0].confidence)
        return (round(avg - abs(half_width), 4), round(avg + abs(half_width), 4))

    # Use spread of agent estimates
    min_mag = min(magnitudes)
    max_mag = max(magnitudes)
    spread = max_mag - min_mag

    # Wider interval when consensus is weak
    consensus = compute_consensus_strength(signals)
    width_multiplier = 1.0 + (1.0 - consensus) * 0.5  # 1.0x at full consensus, 1.5x at zero

    half_width = (spread / 2) * width_multiplier
    lower = avg - half_width
    upper = avg + half_width

    return (round(lower, 4), round(upper, 4))


def determine_conviction(consensus_strength: float, avg_confidence: float) -> str:
    """Determine forecast conviction level.

    Args:
        consensus_strength: How much agents agree (0-1).
        avg_confidence: Average agent confidence (0-1).

    Returns:
        'low', 'medium', or 'high'.
    """
    composite = consensus_strength * 0.6 + avg_confidence * 0.4

    if composite >= 0.65:
        return "high"
    elif composite >= 0.4:
        return "medium"
    else:
        return "low"


def extract_key_drivers(signals: list[Signal], top_n: int = 3) -> list[str]:
    """Extract the top drivers across all agent evidence.

    Prioritizes high-relevance evidence from high-confidence agents.

    Args:
        signals: Agent signals.
        top_n: How many drivers to return.

    Returns:
        List of driver description strings.
    """
    scored_evidence: list[tuple[float, str]] = []

    for signal in signals:
        for evidence in signal.evidence:
            score = evidence.relevance * signal.confidence
            driver = f"[{signal.agent_id}] {evidence.observation} (source: {evidence.source})"
            scored_evidence.append((score, driver))

    scored_evidence.sort(key=lambda x: x[0], reverse=True)
    return [driver for _, driver in scored_evidence[:top_n]]


def extract_key_risks(signals: list[Signal], top_n: int = 3) -> list[str]:
    """Extract the top risks across all agents.

    Args:
        signals: Agent signals.
        top_n: How many risks to return.

    Returns:
        List of risk strings, deduplicated.
    """
    all_risks: list[str] = []
    seen: set[str] = set()

    # Prioritize risks from higher-confidence agents
    sorted_signals = sorted(signals, key=lambda s: s.confidence, reverse=True)
    for signal in sorted_signals:
        for risk in signal.risks:
            normalized = risk.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                all_risks.append(f"[{signal.agent_id}] {risk}")

    return all_risks[:top_n]


def find_dissenting_view(signals: list[Signal]) -> str | None:
    """Find the strongest dissenting view in the swarm.

    The dissenter is the agent whose direction disagrees with the
    majority while having the highest confidence.

    Args:
        signals: Agent signals.

    Returns:
        Description of the dissenting view, or None if unanimous.
    """
    if len(signals) < 2:
        return None

    # Find majority direction
    directions = [s.direction for s in signals]
    direction_counts = {d: directions.count(d) for d in set(directions)}
    majority_direction = max(direction_counts, key=direction_counts.get)  # type: ignore[arg-type]

    # Find dissenters
    dissenters = [s for s in signals if s.direction != majority_direction]
    if not dissenters:
        return None

    # Pick the most confident dissenter
    top_dissenter = max(dissenters, key=lambda s: s.confidence)
    contrarian = top_dissenter.contrarian_note or "No specific contrarian reasoning provided."

    return (
        f"{top_dissenter.agent_id} is {top_dissenter.direction} "
        f"(conf={top_dissenter.confidence}) vs majority {majority_direction}: "
        f"{contrarian}"
    )
