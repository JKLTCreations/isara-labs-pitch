"""Signal protocol — the structured language agents speak."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """A single piece of supporting evidence for a signal."""

    source: str = Field(description="Data origin, e.g. 'yfinance:XAUUSD', 'FRED:GDP'")
    observation: str = Field(description="What the data shows")
    relevance: float = Field(ge=0.0, le=1.0, description="How much this drives the signal")
    timestamp: str = Field(description="When this data was observed, ISO-8601")


class Signal(BaseModel):
    """A structured forecast signal emitted by a specialist agent."""

    agent_id: str = Field(description="Which agent produced this signal")
    asset: str = Field(description="Asset being forecast, e.g. 'XAUUSD', 'CL1'")
    direction: Literal["bullish", "bearish", "neutral"]
    magnitude: float = Field(
        ge=-1.0, le=1.0, description="Expected % move as decimal (-1.0 to 1.0)"
    )
    confidence: float = Field(ge=0.0, le=0.95, description="Calibrated confidence, capped at 0.95")
    horizon: str = Field(description="Forecast horizon, e.g. '7d', '30d', '90d'")
    evidence: list[Evidence] = Field(min_length=1, description="Supporting evidence (non-empty)")
    risks: list[str] = Field(min_length=1, description="What could invalidate this signal")
    contrarian_note: str | None = Field(
        default=None, description="What the consensus might be missing"
    )


class Challenge(BaseModel):
    """A structured critique of another agent's signal during debate."""

    challenger_id: str
    target_id: str
    argument: str = Field(description="The specific critique")
    evidence_gap: str = Field(description="What data the target agent missed or misread")
    suggested_revision: str = Field(description="What the challenger thinks should change")


class Revision(BaseModel):
    """An agent's response to a challenge — either a revision or defense."""

    agent_id: str
    original_direction: Literal["bullish", "bearish", "neutral"]
    original_confidence: float
    revised_signal: Signal | None = Field(
        default=None, description="Updated signal if the agent was persuaded"
    )
    defense: str | None = Field(
        default=None, description="Why the agent is standing firm"
    )
    revision_reason: str | None = Field(
        default=None, description="What convinced the agent to change"
    )


class Forecast(BaseModel):
    """The aggregated consensus forecast produced by the swarm."""

    asset: str
    direction: Literal["bullish", "bearish", "neutral"]
    expected_move: float = Field(description="Point estimate of % move")
    confidence_interval: tuple[float, float] = Field(description="80% confidence interval")
    horizon: str
    conviction: Literal["low", "medium", "high"]
    consensus_strength: float = Field(
        ge=0.0, le=1.0, description="How much agents agreed (0=split, 1=unanimous)"
    )
    key_drivers: list[str] = Field(min_length=1, max_length=5)
    key_risks: list[str] = Field(min_length=1, max_length=5)
    dissenting_view: str | None = Field(
        default=None, description="Strongest counter-argument from debate"
    )
    agent_signals: list[Signal] = Field(description="All signals for full transparency")
    debate_summary: str = Field(description="What agents argued about")
