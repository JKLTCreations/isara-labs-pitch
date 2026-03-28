"""Sentiment and positioning tools for the sentiment analyst agent.

Delegates to the MCP news-sentiment server for cached, standardized data.
"""

from __future__ import annotations

from agents import function_tool

from src.mcp.news_server import (
    get_fear_greed_index as _mcp_fear_greed,
    get_options_sentiment as _mcp_options,
    get_positioning as _mcp_positioning,
    get_sector_rotation as _mcp_sectors,
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


@function_tool
def get_options_sentiment() -> str:
    """Get options market sentiment via VIX term structure and vol ETF flows.

    VIX term structure reveals near-term vs medium-term fear. Volatility
    ETF volume ratios show hedging activity. Backwardation = fear spike,
    contango = complacency.

    Returns:
        JSON with VIX regime, term structure shape, vol ETF activity.
    """
    return _mcp_options()


@function_tool
def get_sector_rotation() -> str:
    """Track sector rotation as a risk appetite signal.

    Compares cyclical sectors (tech, discretionary, industrials) vs
    defensive sectors (utilities, staples, healthcare). Cyclical leadership
    = risk-on environment. Defensive leadership = risk-off.

    Returns:
        JSON with sector returns, rotation spread, risk regime.
    """
    return _mcp_sectors()
