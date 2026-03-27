"""Sentiment and positioning tools for the sentiment analyst agent.

Delegates to the MCP news-sentiment server for cached, standardized data.
"""

from __future__ import annotations

from agents import function_tool

from src.mcp.news_server import (
    get_fear_greed_index as _mcp_fear_greed,
    get_positioning as _mcp_positioning,
    get_sentiment_score as _mcp_sentiment,
)


@function_tool
def get_fear_greed_index() -> str:
    """Get a proxy fear/greed index based on VIX, S&P momentum, and safe haven demand.

    Returns:
        JSON with composite fear/greed score and component breakdown.
    """
    return _mcp_fear_greed()


@function_tool
def get_positioning_data(asset: str) -> str:
    """Get market positioning proxies for an asset via ETF flows and volume.

    Args:
        asset: Asset to check positioning for (e.g., 'gold', 'oil', 'SPX').

    Returns:
        JSON with positioning signals and flow data.
    """
    return _mcp_positioning(asset=asset)


@function_tool
def get_social_sentiment(asset: str, platform: str = "all") -> str:
    """Get social/crowd sentiment proxy for an asset.

    Args:
        asset: Asset to check (e.g., 'gold', 'BTC', 'SPX').
        platform: Platform filter (returns combined proxy).

    Returns:
        JSON with crowd sentiment indicators.
    """
    # Reuse sentiment scoring as social proxy
    return _mcp_sentiment(asset=asset)
