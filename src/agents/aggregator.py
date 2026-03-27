"""Aggregator agent — the Chief Investment Officer.

Synthesizes conflicting specialist signals and debate transcripts
into a single consensus forecast. Has NO data tools — pure synthesis.

Phase 10: Receives calibration profiles for dynamic agent weighting.
Agents with better track records on the specific asset get higher weight.
"""

from __future__ import annotations

import json

from agents import Agent

from src.config import get_config
from src.orchestrator.debate import DebateRound
from src.signals.aggregation import (
    aggregate_direction,
    compute_confidence_interval,
    determine_conviction,
    extract_key_drivers,
    extract_key_risks,
    find_dissenting_view,
)
from src.signals.calibration import CalibrationProfile, format_calibration_context
from src.signals.schema import Forecast, Signal

PROMPT_VERSION = "2.0.0"

AGGREGATOR_SYSTEM_PROMPT = """\
You are the Chief Investment Officer of a multi-agent forecasting swarm. Your job is to \
synthesize conflicting signals from specialist agents into a single, coherent forecast.

You will receive:
1. Signals from each specialist agent (may include geopolitical, macro, sentiment, quant, \
   and sub-specialists like energy, china, or polling)
2. A debate transcript showing how agents challenged each other
3. Pre-computed aggregation metrics (direction consensus, confidence interval, conviction)
4. Agent calibration profiles showing each agent's historical accuracy and calibration quality

Your task: produce a Forecast that represents the swarm's best collective view.

RULES:
1. You do NOT have access to raw data. You work only with agent signals, debate context, \
   and calibration profiles.
2. Weight agents by CALIBRATION QUALITY, not just their raw confidence scores. An agent \
   with calibration_weight=0.9 and 70% accuracy should be trusted more than one with \
   calibration_weight=0.5 and 60% accuracy.
3. When agents are split 2-2, flag this as LOW conviction — do not force a consensus.
4. The debate_summary should explain WHAT agents disagreed about and WHY.
5. The dissenting_view should be the strongest counter-argument.
6. Be honest about uncertainty. A "neutral with low conviction" forecast is better than \
   a fabricated consensus.
7. If a "human_analyst" signal is present, treat it as a high-weight signal — human \
   analysts inject signals when they have strong domain knowledge.
8. Note when an agent appears to be "out of domain" — e.g., a sentiment analyst with \
   very low accuracy on a specific asset should be weighted down.
"""


def build_aggregator_prompt(
    signals: list[Signal],
    debate_rounds: list[DebateRound],
    calibration_profiles: dict[str, CalibrationProfile] | None = None,
) -> str:
    """Build the prompt for the aggregator agent with all context.

    Args:
        signals: Final signals after debate.
        debate_rounds: Debate transcript.
        calibration_profiles: Optional per-agent calibration data for dynamic weighting.

    Returns:
        Full prompt string for the aggregator.
    """
    # Pre-compute aggregation metrics
    direction, weighted_magnitude = aggregate_direction(signals)
    ci = compute_confidence_interval(signals)
    avg_confidence = sum(s.confidence for s in signals) / len(signals) if signals else 0
    from src.orchestrator.rounds import compute_consensus_strength
    consensus = compute_consensus_strength(signals)
    conviction = determine_conviction(consensus, avg_confidence)
    drivers = extract_key_drivers(signals)
    risks = extract_key_risks(signals)
    dissent = find_dissenting_view(signals)

    prompt = "=== SPECIALIST SIGNALS ===\n\n"
    for s in signals:
        prompt += f"--- {s.agent_id} ---\n{json.dumps(s.model_dump(), indent=2)}\n\n"

    if debate_rounds:
        prompt += "=== DEBATE TRANSCRIPT ===\n\n"
        for dr in debate_rounds:
            prompt += f"--- Round {dr.round_number} ---\n"
            prompt += f"Challenges issued: {len(dr.challenges)}\n"
            for c in dr.challenges:
                prompt += f"  {c.challenger_id} -> {c.target_id}: {c.argument}\n"
            prompt += f"Revisions: {len(dr.revisions)}\n"
            for r in dr.revisions:
                if r.revised_signal:
                    prompt += f"  {r.agent_id} REVISED: {r.revision_reason}\n"
                elif r.defense:
                    prompt += f"  {r.agent_id} DEFENDED: {r.defense}\n"
            prompt += "\n"

    # Calibration context (Phase 10)
    if calibration_profiles:
        prompt += format_calibration_context(calibration_profiles)
        prompt += "\n\n"

    prompt += "=== PRE-COMPUTED METRICS ===\n"
    prompt += f"Consensus direction: {direction}\n"
    prompt += f"Weighted magnitude: {weighted_magnitude:.4f}\n"
    prompt += f"Confidence interval (80%): {ci}\n"
    prompt += f"Consensus strength: {consensus:.2f}\n"
    prompt += f"Conviction: {conviction}\n"
    prompt += f"Key drivers: {drivers}\n"
    prompt += f"Key risks: {risks}\n"
    prompt += f"Dissenting view: {dissent}\n\n"

    prompt += (
        "Produce a Forecast that represents the swarm's best collective judgment. "
        "Use the pre-computed metrics as a starting point but adjust based on your "
        "reading of the signals, debate quality, and agent calibration profiles. "
        "Write a concise debate_summary."
    )

    return prompt


def create_aggregator_agent() -> Agent:
    """Create the aggregator (CIO) agent."""
    config = get_config()
    return Agent(
        name="aggregator",
        instructions=AGGREGATOR_SYSTEM_PROMPT,
        model=config.agent_model,
        output_type=Forecast,
    )
