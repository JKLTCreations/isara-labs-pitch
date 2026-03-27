"""Tests for the Signal protocol schemas."""

import pytest
from pydantic import ValidationError

from src.signals.schema import Evidence, Forecast, Signal


class TestEvidence:
    def test_valid_evidence(self):
        e = Evidence(
            source="yfinance:GC=F",
            observation="Gold trading at $2,650",
            relevance=0.8,
            timestamp="2026-03-26T12:00:00",
        )
        assert e.source == "yfinance:GC=F"
        assert e.relevance == 0.8

    def test_relevance_bounds(self):
        with pytest.raises(ValidationError):
            Evidence(source="x", observation="x", relevance=1.5, timestamp="2026-01-01")
        with pytest.raises(ValidationError):
            Evidence(source="x", observation="x", relevance=-0.1, timestamp="2026-01-01")


class TestSignal:
    def _make_evidence(self) -> Evidence:
        return Evidence(
            source="yfinance:GC=F",
            observation="Gold at $2,650",
            relevance=0.7,
            timestamp="2026-03-26T12:00:00",
        )

    def test_valid_signal(self):
        s = Signal(
            agent_id="quant_analyst",
            asset="XAUUSD",
            direction="bullish",
            magnitude=0.05,
            confidence=0.7,
            horizon="30d",
            evidence=[self._make_evidence()],
            risks=["USD strength could cap upside"],
        )
        assert s.direction == "bullish"
        assert s.confidence == 0.7

    def test_confidence_capped_at_095(self):
        with pytest.raises(ValidationError):
            Signal(
                agent_id="quant",
                asset="XAUUSD",
                direction="bullish",
                magnitude=0.05,
                confidence=0.99,
                horizon="30d",
                evidence=[self._make_evidence()],
                risks=["risk"],
            )

    def test_empty_evidence_rejected(self):
        with pytest.raises(ValidationError):
            Signal(
                agent_id="quant",
                asset="XAUUSD",
                direction="bullish",
                magnitude=0.05,
                confidence=0.7,
                horizon="30d",
                evidence=[],
                risks=["risk"],
            )

    def test_empty_risks_rejected(self):
        with pytest.raises(ValidationError):
            Signal(
                agent_id="quant",
                asset="XAUUSD",
                direction="bullish",
                magnitude=0.05,
                confidence=0.7,
                horizon="30d",
                evidence=[self._make_evidence()],
                risks=[],
            )

    def test_magnitude_bounds(self):
        with pytest.raises(ValidationError):
            Signal(
                agent_id="quant",
                asset="XAUUSD",
                direction="bullish",
                magnitude=1.5,
                confidence=0.5,
                horizon="30d",
                evidence=[self._make_evidence()],
                risks=["risk"],
            )
