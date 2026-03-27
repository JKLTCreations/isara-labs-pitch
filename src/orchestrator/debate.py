"""Adversarial debate protocol.

Agents review each other's signals, issue challenges, and revise
or defend their positions. This is what prevents groupthink.

Includes structured logging and graceful degradation on failures.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field

from agents import Agent, Runner

from src.config import get_config
from src.logging import get_logger
from src.signals.schema import Challenge, Revision, Signal

log = get_logger()

CHALLENGER_PROMPT_VERSION = "1.0.0"

CHALLENGE_SYSTEM_PROMPT = """\
You are participating in an adversarial debate round as part of a forecasting swarm. \
Your job is to CHALLENGE the signal you disagree with most.

You will receive:
1. Your own signal (what you believe)
2. All other agents' signals

Your task: identify the signal that is MOST WRONG and write a structured Challenge. \
Be specific — cite evidence gaps, logical flaws, or data the other agent ignored. \
Do not be polite. Be rigorous. The quality of the swarm depends on genuine disagreement.

If you actually agree with all other signals, challenge the one with the weakest evidence \
(highest confidence relative to evidence quality).
"""

REVISION_SYSTEM_PROMPT = """\
You are responding to a challenge against your forecast signal. Another agent has \
identified flaws in your analysis.

You will receive:
1. Your original signal
2. The challenge against it

You have two options:
1. REVISE: Update your signal if the challenge is valid. Produce a new Signal with adjusted \
   direction, magnitude, or confidence. Explain what convinced you.
2. DEFEND: Stand firm if the challenge is wrong. Explain specifically why the challenger's \
   critique doesn't hold, citing your evidence.

Be honest. If the challenge reveals a genuine blind spot, revise. If it doesn't, defend. \
Stubbornness and capitulation are both failures.
"""


@dataclass
class DebateRound:
    """Record of a single debate round."""

    round_number: int
    challenges: list[Challenge]
    revisions: list[Revision]
    revised_signals: list[Signal]


async def _generate_challenge(
    agent: Agent,
    own_signal: Signal,
    all_signals: list[Signal],
    timeout: int,
) -> Challenge | None:
    """Have an agent challenge the signal it disagrees with most."""
    config = get_config()

    other_signals = [s for s in all_signals if s.agent_id != own_signal.agent_id]
    if not other_signals:
        return None

    prompt = (
        f"YOUR SIGNAL:\n{json.dumps(own_signal.model_dump(), indent=2)}\n\n"
        f"OTHER AGENTS' SIGNALS:\n"
    )
    for s in other_signals:
        prompt += f"\n--- {s.agent_id} ---\n{json.dumps(s.model_dump(), indent=2)}\n"

    prompt += (
        f"\nChallenge the signal you disagree with most. "
        f"Set challenger_id to '{own_signal.agent_id}'."
    )

    challenge_agent = Agent(
        name=f"{agent.name}_challenger",
        instructions=CHALLENGE_SYSTEM_PROMPT,
        model=config.agent_model,
        output_type=Challenge,
    )

    try:
        result = await asyncio.wait_for(
            Runner.run(challenge_agent, input=prompt),
            timeout=timeout,
        )
        challenge = result.final_output_as(Challenge)
        log.debug(
            "challenge_generated",
            challenger=own_signal.agent_id,
            target=challenge.target_id,
            phase="debate",
        )
        return challenge
    except asyncio.TimeoutError:
        log.warning(
            "challenge_timeout",
            agent_id=own_signal.agent_id,
            timeout=timeout,
            phase="debate",
        )
        return None
    except Exception as e:
        log.warning(
            "challenge_failed",
            agent_id=own_signal.agent_id,
            error=str(e),
            phase="debate",
        )
        return None


async def _generate_revision(
    agent: Agent,
    original_signal: Signal,
    challenge: Challenge,
    timeout: int,
) -> Revision | None:
    """Have a challenged agent revise or defend their signal."""
    config = get_config()

    prompt = (
        f"YOUR ORIGINAL SIGNAL:\n{json.dumps(original_signal.model_dump(), indent=2)}\n\n"
        f"CHALLENGE AGAINST YOU (from {challenge.challenger_id}):\n"
        f"{json.dumps(challenge.model_dump(), indent=2)}\n\n"
        f"Revise your signal or defend it. "
        f"Set agent_id to '{original_signal.agent_id}'. "
        f"If revising, produce a complete new Signal in the revised_signal field."
    )

    revision_agent = Agent(
        name=f"{agent.name}_reviser",
        instructions=REVISION_SYSTEM_PROMPT,
        model=config.agent_model,
        tools=agent.tools,
        output_type=Revision,
    )

    try:
        result = await asyncio.wait_for(
            Runner.run(revision_agent, input=prompt),
            timeout=timeout,
        )
        revision = result.final_output_as(Revision)
        action = "revised" if revision.revised_signal else "defended"
        log.debug(
            "revision_generated",
            agent_id=original_signal.agent_id,
            action=action,
            phase="debate",
        )
        return revision
    except asyncio.TimeoutError:
        log.warning(
            "revision_timeout",
            agent_id=original_signal.agent_id,
            timeout=timeout,
            phase="debate",
        )
        return None
    except Exception as e:
        log.warning(
            "revision_failed",
            agent_id=original_signal.agent_id,
            error=str(e),
            phase="debate",
        )
        return None


async def run_debate_round(
    agents: list[Agent],
    signals: list[Signal],
    round_number: int,
    timeout: int = 60,
) -> DebateRound:
    """Run one round of adversarial debate.

    1. Each agent challenges the signal it disagrees with most.
    2. Challenged agents revise or defend.
    3. Returns updated signals.

    Graceful degradation: if some challenges/revisions fail,
    the round continues with whatever succeeded.

    Args:
        agents: The specialist agents.
        signals: Current signals from each agent.
        round_number: Which debate round this is (1-indexed).
        timeout: Per-agent timeout in seconds.

    Returns:
        DebateRound with challenges, revisions, and updated signals.
    """
    # Build agent lookup
    agent_map: dict[str, Agent] = {a.name: a for a in agents}
    signal_map: dict[str, Signal] = {s.agent_id: s for s in signals}

    log.debug(
        "debate_round_started",
        round=round_number,
        agents=len(agents),
        phase="debate",
    )

    # Phase 1: All agents generate challenges in parallel
    challenge_tasks = []
    for agent in agents:
        own_signal = signal_map.get(agent.name)
        if own_signal:
            challenge_tasks.append(
                _generate_challenge(agent, own_signal, signals, timeout)
            )

    challenge_results = await asyncio.gather(*challenge_tasks, return_exceptions=True)
    challenges: list[Challenge] = [
        c for c in challenge_results if isinstance(c, Challenge)
    ]

    if not challenges:
        log.warning(
            "no_challenges_produced",
            round=round_number,
            phase="debate",
        )
        return DebateRound(
            round_number=round_number,
            challenges=[],
            revisions=[],
            revised_signals=list(signals),
        )

    # Phase 2: Challenged agents respond
    # Group challenges by target
    challenges_by_target: dict[str, list[Challenge]] = {}
    for c in challenges:
        challenges_by_target.setdefault(c.target_id, []).append(c)

    revision_tasks = []
    revision_agent_ids: list[str] = []

    for target_id, target_challenges in challenges_by_target.items():
        target_agent = agent_map.get(target_id)
        target_signal = signal_map.get(target_id)
        if target_agent and target_signal:
            # Respond to the strongest challenge (first one)
            revision_tasks.append(
                _generate_revision(target_agent, target_signal, target_challenges[0], timeout)
            )
            revision_agent_ids.append(target_id)

    revision_results = await asyncio.gather(*revision_tasks, return_exceptions=True)
    revisions: list[Revision] = [
        r for r in revision_results if isinstance(r, Revision)
    ]

    # Phase 3: Build updated signal list
    revised_signals = list(signals)  # Start with originals
    for revision in revisions:
        if revision.revised_signal is not None:
            # Agent was persuaded — swap in the revised signal
            revised_signals = [
                revision.revised_signal if s.agent_id == revision.agent_id else s
                for s in revised_signals
            ]

    return DebateRound(
        round_number=round_number,
        challenges=challenges,
        revisions=revisions,
        revised_signals=revised_signals,
    )
