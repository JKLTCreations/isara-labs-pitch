"""Base agent template — create specialist agents from configuration dictionaries.

New agents can be defined as data (system prompt + tool list + name) rather than
writing a new Python module each time. This enables rapid creation of
sub-specialists without touching orchestration logic.

Usage:
    from src.agents.templates.base import create_agent_from_template

    agent = create_agent_from_template(
        name="energy_analyst",
        system_prompt="You are an energy sector specialist...",
        tools=[search_news, get_price_data],
        model_override=None,  # Uses config.agent_model by default
    )
"""

from __future__ import annotations

from typing import Any

from agents import Agent

from src.config import get_config
from src.signals.schema import Signal


def create_agent_from_template(
    name: str,
    system_prompt: str,
    tools: list[Any] | None = None,
    model_override: str | None = None,
) -> Agent:
    """Create a specialist agent from a template configuration.

    Args:
        name: Agent identifier (e.g., 'energy_analyst').
        system_prompt: Full system instructions including cognitive bias.
        tools: List of @function_tool decorated tools. Empty list = no tools.
        model_override: Override the default model from config.

    Returns:
        Configured Agent that emits Signal objects.
    """
    config = get_config()
    return Agent(
        name=name,
        instructions=system_prompt,
        model=model_override or config.agent_model,
        tools=tools or [],
        output_type=Signal,
    )
