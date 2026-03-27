"""Agent registry — factory for creating and managing specialist agents.

Supports both core agents and dynamically-registered sub-specialists.
The triage agent uses this registry to instantiate the optimal swarm
composition for each forecast request.
"""

from __future__ import annotations

from collections.abc import Callable

from agents import Agent

from src.agents.china import create_china_agent
from src.agents.energy import create_energy_agent
from src.agents.geopolitical import create_geopolitical_agent
from src.agents.macro import create_macro_agent
from src.agents.polling import create_polling_agent
from src.agents.quant import create_quant_agent
from src.agents.sentiment import create_sentiment_agent

# All available specialist agent factories
AGENT_FACTORIES: dict[str, Callable[[], Agent]] = {
    # Core agents (Phase 2)
    "quant_analyst": create_quant_agent,
    "geopolitical_analyst": create_geopolitical_agent,
    "macro_economist": create_macro_agent,
    "sentiment_analyst": create_sentiment_agent,
    # Sub-specialists (Phase 9)
    "energy_analyst": create_energy_agent,
    "china_analyst": create_china_agent,
    "polling_analyst": create_polling_agent,
}

# Default swarm composition (used when no triage is performed)
DEFAULT_SWARM = [
    "geopolitical_analyst",
    "macro_economist",
    "sentiment_analyst",
    "quant_analyst",
]


def register_agent(agent_id: str, factory: Callable[[], Agent]) -> None:
    """Register a new agent factory at runtime.

    This enables dynamic agent registration from templates or plugins
    without modifying this module.

    Args:
        agent_id: Unique agent identifier.
        factory: Callable that returns an Agent instance.
    """
    AGENT_FACTORIES[agent_id] = factory


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
