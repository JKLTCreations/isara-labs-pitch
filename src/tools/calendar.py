"""Economic calendar tool.

Provides a static calendar of major recurring economic events
and known upcoming dates. In production, this would connect to
an economic calendar API.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from agents import function_tool

# Major recurring economic events (approximate schedule)
RECURRING_EVENTS = [
    {"event": "FOMC Rate Decision", "frequency": "~6 weeks", "impact": "high", "affects": ["rates", "USD", "gold", "equities"]},
    {"event": "US Non-Farm Payrolls", "frequency": "monthly (first Friday)", "impact": "high", "affects": ["USD", "rates", "equities"]},
    {"event": "US CPI Release", "frequency": "monthly (~12th)", "impact": "high", "affects": ["rates", "gold", "USD"]},
    {"event": "US GDP (Advance)", "frequency": "quarterly", "impact": "high", "affects": ["USD", "rates", "equities"]},
    {"event": "ECB Rate Decision", "frequency": "~6 weeks", "impact": "high", "affects": ["EUR", "USD", "European equities"]},
    {"event": "BOJ Rate Decision", "frequency": "~6 weeks", "impact": "medium", "affects": ["JPY", "USD"]},
    {"event": "OPEC+ Meeting", "frequency": "~monthly", "impact": "high", "affects": ["oil", "energy equities"]},
    {"event": "US PCE Price Index", "frequency": "monthly", "impact": "high", "affects": ["rates", "gold", "USD"]},
    {"event": "US ISM Manufacturing PMI", "frequency": "monthly (first business day)", "impact": "medium", "affects": ["USD", "equities"]},
    {"event": "US Retail Sales", "frequency": "monthly (~15th)", "impact": "medium", "affects": ["USD", "equities"]},
    {"event": "China PMI (Official)", "frequency": "monthly (last day)", "impact": "medium", "affects": ["CNY", "commodities", "emerging markets"]},
    {"event": "US Jobless Claims", "frequency": "weekly (Thursday)", "impact": "low-medium", "affects": ["USD", "rates"]},
]


@function_tool
def get_economic_calendar(region: str = "global", horizon: str = "30d") -> str:
    """Get upcoming economic events that could impact forecasts.

    Args:
        region: Filter by region ('global', 'US', 'EU', 'Asia').
        horizon: How far ahead to look (e.g., '7d', '30d').

    Returns:
        JSON with upcoming events, their expected impact, and affected assets.
    """
    region_filters: dict[str, list[str]] = {
        "US": ["US ", "FOMC"],
        "EU": ["ECB", "EU "],
        "Asia": ["BOJ", "China"],
        "global": [],  # No filter — return all
    }

    keywords = region_filters.get(region, [])

    events = []
    for event in RECURRING_EVENTS:
        if keywords and not any(kw in event["event"] for kw in keywords):
            continue
        events.append(event)

    days = int(horizon.rstrip("d"))
    now = datetime.now()

    return json.dumps({
        "region": region,
        "horizon": horizon,
        "period": f"{now.strftime('%Y-%m-%d')} to {(now + timedelta(days=days)).strftime('%Y-%m-%d')}",
        "event_count": len(events),
        "events": events,
        "note": "Static calendar. Dates are approximate recurring schedules, not exact upcoming dates. Use a calendar API for precise scheduling.",
        "timestamp": now.isoformat(),
    })
