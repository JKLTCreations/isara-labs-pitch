"""Tests for convergence detection and consensus strength."""

from src.orchestrator.rounds import compute_consensus_strength, convergence_detected
from src.signals.schema import Evidence, Signal


def _make_signal(
    agent_id: str,
    direction: str = "bullish",
    confidence: float = 0.7,
) -> Signal:
    return Signal(
        agent_id=agent_id,
        asset="XAUUSD",
        direction=direction,
        magnitude=0.05 if direction == "bullish" else -0.05 if direction == "bearish" else 0.0,
        confidence=confidence,
        horizon="30d",
        evidence=[
            Evidence(source="test", observation="test", relevance=0.5, timestamp="2026-01-01")
        ],
        risks=["test risk"],
    )


class TestConvergence:
    def test_converged_when_all_agree_and_stable(self):
        prev = [
            _make_signal("a", "bullish", 0.7),
            _make_signal("b", "bullish", 0.6),
            _make_signal("c", "bullish", 0.8),
            _make_signal("d", "bullish", 0.5),
        ]
        curr = [
            _make_signal("a", "bullish", 0.72),
            _make_signal("b", "bullish", 0.62),
            _make_signal("c", "bullish", 0.78),
            _make_signal("d", "bullish", 0.52),
        ]
        assert convergence_detected(prev, curr) is True

    def test_not_converged_when_split(self):
        prev = [
            _make_signal("a", "bullish", 0.7),
            _make_signal("b", "bearish", 0.6),
            _make_signal("c", "bullish", 0.8),
            _make_signal("d", "bearish", 0.5),
        ]
        curr = [
            _make_signal("a", "bullish", 0.7),
            _make_signal("b", "bearish", 0.6),
            _make_signal("c", "bullish", 0.8),
            _make_signal("d", "bearish", 0.5),
        ]
        assert convergence_detected(prev, curr) is False

    def test_not_converged_when_confidence_shifts(self):
        prev = [
            _make_signal("a", "bullish", 0.7),
            _make_signal("b", "bullish", 0.6),
            _make_signal("c", "bullish", 0.8),
            _make_signal("d", "bullish", 0.5),
        ]
        curr = [
            _make_signal("a", "bullish", 0.7),
            _make_signal("b", "bullish", 0.6),
            _make_signal("c", "bullish", 0.5),  # Shifted by 0.3 — too much
            _make_signal("d", "bullish", 0.5),
        ]
        assert convergence_detected(prev, curr) is False

    def test_converged_with_3_of_4_agreeing(self):
        prev = [
            _make_signal("a", "bullish", 0.7),
            _make_signal("b", "bullish", 0.6),
            _make_signal("c", "bullish", 0.8),
            _make_signal("d", "bearish", 0.5),
        ]
        curr = [
            _make_signal("a", "bullish", 0.72),
            _make_signal("b", "bullish", 0.62),
            _make_signal("c", "bullish", 0.78),
            _make_signal("d", "bearish", 0.52),
        ]
        assert convergence_detected(prev, curr) is True

    def test_empty_signals_converge(self):
        assert convergence_detected([], []) is True


class TestConsensusStrength:
    def test_unanimous_high_confidence(self):
        signals = [
            _make_signal("a", "bullish", 0.9),
            _make_signal("b", "bullish", 0.8),
            _make_signal("c", "bullish", 0.7),
        ]
        strength = compute_consensus_strength(signals)
        assert strength > 0.7

    def test_split_low_strength(self):
        signals = [
            _make_signal("a", "bullish", 0.8),
            _make_signal("b", "bearish", 0.8),
        ]
        strength = compute_consensus_strength(signals)
        assert strength < 0.3

    def test_empty_returns_zero(self):
        assert compute_consensus_strength([]) == 0.0
