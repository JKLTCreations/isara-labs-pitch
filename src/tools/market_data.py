"""Market data tools for the quantitative analyst agent.

Delegates to the MCP market-data server for cached, standardized data.
"""

from __future__ import annotations

from agents import function_tool

from src.mcp.market_server import (
    get_correlation_matrix as _mcp_corr,
    get_price_data as _mcp_price,
    get_technical_indicators as _mcp_tech,
    get_volatility as _mcp_vol,
)


@function_tool
def get_price_data(asset: str, horizon: str = "30d") -> str:
    """Fetch recent OHLCV price data for an asset.

    Args:
        asset: Asset identifier (e.g., 'XAUUSD', 'gold', 'CL1', 'SPX').
        horizon: Forecast horizon to determine lookback period (e.g., '30d', '90d').

    Returns:
        JSON string with price summary and recent data points.
    """
    return _mcp_price(asset=asset, horizon=horizon)


@function_tool
def get_technical_indicators(asset: str, horizon: str = "30d") -> str:
    """Calculate key technical indicators for an asset.

    Args:
        asset: Asset identifier (e.g., 'XAUUSD', 'gold', 'CL1').
        horizon: Forecast horizon (e.g., '30d', '90d').

    Returns:
        JSON string with RSI, moving averages, Bollinger bands, and MACD.
    """
    return _mcp_tech(asset=asset, horizon=horizon)


@function_tool
def get_volatility(asset: str) -> str:
    """Get historical volatility metrics across multiple timeframes.

    Args:
        asset: Asset identifier (e.g., 'XAUUSD', 'SPX', 'BTC').

    Returns:
        JSON string with 5d/20d/60d/1y volatility and regime classification.
    """
    return _mcp_vol(asset=asset)


@function_tool
def get_correlation_matrix(assets: str, period: str = "3mo") -> str:
    """Compute correlation matrix between multiple assets.

    Args:
        assets: Comma-separated asset list (e.g., 'XAUUSD,DXY,SPX,TLT').
        period: Lookback period (e.g., '1mo', '3mo', '6mo').

    Returns:
        JSON string with correlation matrix and notable pairs.
    """
    return _mcp_corr(assets=assets, period=period)
