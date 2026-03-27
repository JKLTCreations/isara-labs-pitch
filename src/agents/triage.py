"""Triage Agent — dynamically selects which specialist agents to spawn.

Instead of always running the default 4-agent swarm, the triage agent
examines the forecast request (asset, horizon, context) and decides
which combination of specialists is most relevant.

This enables asset-specific agent composition:
  - Gold  → geopolitical + macro + sentiment + quant (standard)
  - Oil   → geopolitical + macro + quant + energy specialist
  - CNY   → geopolitical + macro + china specialist + quant
  - Election → geopolitical + sentiment + polling specialist + macro
"""

from __future__ import annotations

# Mapping from asset identifiers to the optimal swarm composition.
# Each value is a list of agent_ids that will be looked up in the registry.
ASSET_SWARM_MAP: dict[str, list[str]] = {
    # Precious metals — geopolitics and sentiment are key drivers
    "XAUUSD": ["geopolitical_analyst", "macro_economist", "sentiment_analyst", "quant_analyst"],
    "gold": ["geopolitical_analyst", "macro_economist", "sentiment_analyst", "quant_analyst"],
    "XAGUSD": ["geopolitical_analyst", "macro_economist", "sentiment_analyst", "quant_analyst"],
    "silver": ["geopolitical_analyst", "macro_economist", "sentiment_analyst", "quant_analyst"],

    # Energy — replace sentiment with energy specialist
    "CL1": ["geopolitical_analyst", "macro_economist", "quant_analyst", "energy_analyst"],
    "oil": ["geopolitical_analyst", "macro_economist", "quant_analyst", "energy_analyst"],

    # China/CNY — replace sentiment with china specialist
    "CNY": ["geopolitical_analyst", "macro_economist", "quant_analyst", "china_analyst"],

    # Equities — standard swarm
    "SPX": ["geopolitical_analyst", "macro_economist", "sentiment_analyst", "quant_analyst"],
    "NDX": ["geopolitical_analyst", "macro_economist", "sentiment_analyst", "quant_analyst"],

    # Fixed income — macro-heavy
    "TLT": ["macro_economist", "sentiment_analyst", "quant_analyst", "geopolitical_analyst"],

    # FX — standard swarm, macro-heavy
    "DXY": ["macro_economist", "geopolitical_analyst", "sentiment_analyst", "quant_analyst"],
    "EUR": ["macro_economist", "geopolitical_analyst", "sentiment_analyst", "quant_analyst"],
    "GBP": ["macro_economist", "geopolitical_analyst", "sentiment_analyst", "quant_analyst"],
    "JPY": ["macro_economist", "geopolitical_analyst", "sentiment_analyst", "quant_analyst"],

    # Crypto — sentiment-heavy
    "BTC": ["sentiment_analyst", "quant_analyst", "macro_economist", "geopolitical_analyst"],
}

# Known correlated asset groups — used for multi-swarm runs
CORRELATED_GROUPS: dict[str, list[str]] = {
    "XAUUSD": ["XAUUSD", "DXY", "TLT"],
    "gold": ["gold", "DXY", "TLT"],
    "CL1": ["CL1", "DXY", "SPX"],
    "oil": ["oil", "DXY", "SPX"],
    "SPX": ["SPX", "TLT", "DXY"],
    "BTC": ["BTC", "SPX", "DXY"],
}

# Default swarm for any asset not in the map
DEFAULT_SWARM = ["geopolitical_analyst", "macro_economist", "sentiment_analyst", "quant_analyst"]


def select_agents(asset: str, context: str | None = None) -> list[str]:
    """Select which specialist agents to spawn for a forecast request.

    The triage logic examines the asset and optional context to decide
    the optimal swarm composition.

    Args:
        asset: Asset identifier (e.g., 'XAUUSD', 'CL1', 'CNY').
        context: Optional additional context (e.g., 'election impact on gold').

    Returns:
        List of agent IDs to spawn.
    """
    # Start with asset-based selection
    agent_ids = list(ASSET_SWARM_MAP.get(asset, DEFAULT_SWARM))

    # Context-based overrides
    if context:
        ctx_lower = context.lower()

        # Election-related context → add polling specialist
        election_keywords = {"election", "vote", "polling", "ballot", "candidate", "primary"}
        if any(kw in ctx_lower for kw in election_keywords):
            if "polling_analyst" not in agent_ids:
                # Replace the least relevant agent (usually the 4th)
                if len(agent_ids) >= 4:
                    agent_ids[3] = "polling_analyst"
                else:
                    agent_ids.append("polling_analyst")

        # China-related context → add china specialist
        china_keywords = {"china", "pboc", "cny", "yuan", "renminbi", "beijing"}
        if any(kw in ctx_lower for kw in china_keywords):
            if "china_analyst" not in agent_ids:
                if len(agent_ids) >= 4:
                    agent_ids[3] = "china_analyst"
                else:
                    agent_ids.append("china_analyst")

        # Energy-related context → add energy specialist
        energy_keywords = {"opec", "energy", "crude", "refinery", "pipeline", "lng"}
        if any(kw in ctx_lower for kw in energy_keywords):
            if "energy_analyst" not in agent_ids:
                if len(agent_ids) >= 4:
                    agent_ids[3] = "energy_analyst"
                else:
                    agent_ids.append("energy_analyst")

    return agent_ids


def get_correlated_assets(asset: str) -> list[str]:
    """Get the correlated asset group for multi-swarm runs.

    Args:
        asset: Primary asset identifier.

    Returns:
        List of correlated assets including the primary asset.
        Returns just the primary asset if no known correlations.
    """
    return CORRELATED_GROUPS.get(asset, [asset])
