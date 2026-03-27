"""News tools for the geopolitical and sentiment agents.

Delegates to the MCP news-sentiment server for cached, standardized data.
"""

from __future__ import annotations

from agents import function_tool

from src.mcp.news_server import (
    get_sentiment_score as _mcp_sentiment,
    search_news as _mcp_search,
)


@function_tool
def search_news(query: str, region: str = "global", days_back: int = 7) -> str:
    """Search recent news articles relevant to a forecast.

    Args:
        query: Search query (e.g., 'gold prices', 'US China trade').
        region: Geographic focus ('global', 'US', 'EU', 'Asia', 'Middle East').
        days_back: How far back to search (1-30 days).

    Returns:
        JSON with news summaries and metadata.
    """
    return _mcp_search(query=query, region=region, days_back=days_back)


@function_tool
def get_news_sentiment(asset: str, days_back: int = 7) -> str:
    """Get aggregated news sentiment for an asset.

    Args:
        asset: Asset name (e.g., 'gold', 'oil', 'SPX').
        days_back: How many days of news to analyze.

    Returns:
        JSON with sentiment summary derived from recent headlines.
    """
    return _mcp_sentiment(asset=asset, days_back=days_back)
