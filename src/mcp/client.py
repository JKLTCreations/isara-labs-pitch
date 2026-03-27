"""MCP client utilities for connecting agents to MCP data servers.

In production, agents would connect to MCP servers over stdio/SSE.
For simplicity, this module provides direct function imports from
the MCP server modules, giving agents the same interface without
requiring a running server process.

This allows:
1. MCP servers to be tested standalone (python -m src.mcp.market_server)
2. Agent tools to call the same cached functions directly
3. Easy migration to true MCP transport later
"""

from __future__ import annotations

# Re-export MCP server tools as callable functions.
# These are the actual implementations with caching built in.

from src.mcp.fred_server import (
    get_inflation_breakdown as mcp_get_inflation_breakdown,
    get_rate_expectations as mcp_get_rate_expectations,
    get_series as mcp_get_fred_series,
)
from src.mcp.market_server import (
    get_correlation_matrix as mcp_get_correlation_matrix,
    get_price_data as mcp_get_price_data,
    get_technical_indicators as mcp_get_technical_indicators,
    get_volatility as mcp_get_volatility,
)
from src.mcp.news_server import (
    get_fear_greed_index as mcp_get_fear_greed_index,
    get_positioning as mcp_get_positioning,
    get_sentiment_score as mcp_get_sentiment_score,
    search_news as mcp_search_news,
)

__all__ = [
    "mcp_get_price_data",
    "mcp_get_technical_indicators",
    "mcp_get_volatility",
    "mcp_get_correlation_matrix",
    "mcp_get_fred_series",
    "mcp_get_rate_expectations",
    "mcp_get_inflation_breakdown",
    "mcp_search_news",
    "mcp_get_sentiment_score",
    "mcp_get_fear_greed_index",
    "mcp_get_positioning",
]
