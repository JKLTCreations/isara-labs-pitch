"""Agent registry — factory for creating and managing specialist agents."""

from __future__ import annotations

from agents import Agent

from src.agents.geopolitical import create_geopolitical_agent
from src.agents.macro import create_macro_agent
from src.agents.quant import create_quant_agent
from src.agents.sentiment import create_sentiment_agent

# All available specialist agent factories
AGENT_FACTORIES: dict[str, callable] = {
    "quant_analyst": create_quant_agent,
    "geopolitical_analyst": create_geopolitical_agent,
    "macro_economist": create_macro_agent,
    "sentiment_analyst": create_sentiment_agent,
}

# Default swarm composition
DEFAULT_SWARM = [
    "geopolitical_analyst",
    "macro_economist",
    "sentiment_analyst",
    "quant_analyst",
]


def create_swarm(agent_ids: list[str] | None = None) -> list[Agent]:
    """Create a list of specialist agents for a forecast run.

    Args:
        agent_ids: Which agents to include. Defaults to the full swarm.

    Returns:
        List of instantiated Agent objects.
    """
    ids = agent_ids or DEFAULT_SWARM
    agents = []
    for agent_id in ids:
        factory = AGENT_FACTORIES.get(agent_id)
        if factory is None:
            raise ValueError(f"Unknown agent: {agent_id}. Available: {list(AGENT_FACTORIES.keys())}")
        agents.append(factory())
    return agents


def list_agents() -> list[str]:
    """Return all available agent IDs."""
    return list(AGENT_FACTORIES.keys())
