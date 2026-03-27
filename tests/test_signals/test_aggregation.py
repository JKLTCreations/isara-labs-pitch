"""Tests for signal aggregation logic."""

from src.signals.aggregation import (
    aggregate_direction,
    compute_confidence_interval,
    determine_conviction,
    extract_key_drivers,
    extract_key_risks,
    find_dissenting_view,
)
from src.signals.schema import Evidence, Signal


def _make_signal(
    agent_id: str,
    direction: str = "bullish",
    magnitude: float = 0.05,
    confidence: float = 0.7,
) -> Signal:
    return Signal(
        agent_id=agent_id,
        asset="XAUUSD",
        direction=direction,
        magnitude=magnitude,
        confidence=confidence,
        horizon="30d",
        evidence=[
            Evidence(
                source=f"{agent_id}:data",
                observation=f"Test observation from {agent_id}",
                relevance=0.8,
                timestamp="2026-03-26T12:00:00",
            )
        ],
        risks=[f"Risk from {agent_id}"],
    )


class TestAggregateDirection:
    def test_unanimous_bullish(self):
        signals = [
            _make_signal("a", "bullish", 0.05, 0.8),
            _make_signal("b", "bullish", 0.03, 0.7),
            _make_signal("c", "bullish", 0.04, 0.6),
        ]
        direction, magnitude = aggregate_direction(signals)
        assert direction == "bullish"
        assert magnitude > 0

    def test_unanimous_bearish(self):
        signals = [
            _make_signal("a", "bearish", -0.05, 0.8),
            _make_signal("b", "bearish", -0.03, 0.7),
        ]
        direction, magnitude = aggregate_direction(signals)
        assert direction == "bearish"
        assert magnitude < 0

    def test_split_resolves_by_confidence(self):
        signals = [
            _make_signal("a", "bullish", 0.05, 0.9),
            _make_signal("b", "bearish", -0.05, 0.3),
        ]
        direction, _ = aggregate_direction(signals)
        assert direction == "bullish"  # Higher confidence bullish wins

    def test_neutral_when_balanced(self):
        signals = [
            _make_signal("a", "bullish", 0.05, 0.5),
            _make_signal("b", "bearish", -0.05, 0.5),
        ]
        direction, _ = aggregate_direction(signals)
        assert direction == "neutral"

    def test_empty_signals(self):
        direction, magnitude = aggregate_direction([])
        assert direction == "neutral"
        assert magnitude == 0.0


class TestConfidenceInterval:
    def test_tight_interval_on_consensus(self):
        signals = [
            _make_signal("a", "bullish", 0.05, 0.9),
            _make_signal("b", "bullish", 0.04, 0.8),
        ]
        lower, upper = compute_confidence_interval(signals)
        assert lower < upper
        assert lower > 0  # Both bullish, interval should be positive

    def test_wider_interval_on_disagreement(self):
        agree_signals = [
            _make_signal("a", "bullish", 0.05, 0.9),
            _make_signal("b", "bullish", 0.04, 0.8),
        ]
        disagree_signals = [
            _make_signal("a", "bullish", 0.10, 0.5),
            _make_signal("b", "bearish", -0.10, 0.5),
        ]
        _, agree_upper = compute_confidence_interval(agree_signals)
        agree_lower, _ = compute_confidence_interval(agree_signals)
        _, disagree_upper = compute_confidence_interval(disagree_signals)
        disagree_lower, _ = compute_confidence_interval(disagree_signals)

        agree_width = agree_upper - agree_lower
        disagree_width = disagree_upper - disagree_lower
        assert disagree_width > agree_width


class TestConviction:
    def test_high_conviction(self):
        assert determine_conviction(0.9, 0.8) == "high"

    def test_low_conviction(self):
        assert determine_conviction(0.1, 0.3) == "low"

    def test_medium_conviction(self):
        assert determine_conviction(0.5, 0.5) == "medium"


class TestDissent:
    def test_finds_dissenter(self):
        signals = [
            _make_signal("a", "bullish", 0.05, 0.8),
            _make_signal("b", "bullish", 0.03, 0.7),
            _make_signal("c", "bearish", -0.04, 0.6),
        ]
        dissent = find_dissenting_view(signals)
        assert dissent is not None
        assert "c" in dissent
        assert "bearish" in dissent

    def test_no_dissent_when_unanimous(self):
        signals = [
            _make_signal("a", "bullish", 0.05, 0.8),
            _make_signal("b", "bullish", 0.03, 0.7),
        ]
        dissent = find_dissenting_view(signals)
        assert dissent is None

    def test_picks_highest_confidence_dissenter(self):
        signals = [
            _make_signal("a", "bullish", 0.05, 0.8),
            _make_signal("b", "bullish", 0.03, 0.7),
            _make_signal("c", "bearish", -0.04, 0.3),
            _make_signal("d", "bearish", -0.06, 0.9),
        ]
        dissent = find_dissenting_view(signals)
        assert dissent is not None
        assert "d" in dissent  # Higher confidence dissenter


class TestDriversAndRisks:
    def test_extracts_drivers(self):
        signals = [
            _make_signal("a", "bullish", 0.05, 0.9),
            _make_signal("b", "bearish", -0.03, 0.5),
        ]
        drivers = extract_key_drivers(signals, top_n=2)
        assert len(drivers) == 2
        assert "a" in drivers[0]  # Higher confidence agent's evidence first

    def test_extracts_risks(self):
        signals = [
            _make_signal("a", "bullish", 0.05, 0.9),
            _make_signal("b", "bearish", -0.03, 0.5),
        ]
        risks = extract_key_risks(signals, top_n=2)
        assert len(risks) == 2
