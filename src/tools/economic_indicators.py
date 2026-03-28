"""Economic indicator tools for the macro-economics agent.

Delegates to the MCP fred-economic server for cached, standardized data.
"""

from __future__ import annotations

from agents import function_tool

from src.mcp.fred_server import (
    get_credit_spreads as _mcp_credit,
    get_inflation_breakdown as _mcp_inflation,
    get_rate_expectations as _mcp_rates,
    get_series as _mcp_series,
    get_treasury_curve as _mcp_curve,
)


@function_tool
def get_fred_series(series_id: str, period: str = "1y") -> str:
    """Fetch a FRED economic data series.

    Common series: GDP, CPIAUCSL, UNRATE, FEDFUNDS, DGS10, DGS2,
    T10Y2Y, DCOILWTICO, GOLDAMGBD228NLBM, DTWEXBGS, M2SL, PCEPI.

    Args:
        series_id: FRED series identifier.
        period: Lookback period ('6mo', '1y', '2y', '5y').

    Returns:
        JSON with recent values and trend summary.
    """
    return _mcp_series(series_id=series_id, period=period)


@function_tool
def get_rate_expectations(currency: str = "USD") -> str:
    """Get current interest rate environment and expectations.

    Args:
        currency: Currency code (currently supports 'USD').

    Returns:
        JSON with current rates, yield curve shape, and rate trend.
    """
    return _mcp_rates(currency=currency)


@function_tool
def get_inflation_breakdown(country: str = "US") -> str:
    """Get inflation-related indicators.

    Args:
        country: Country code (currently supports 'US').

    Returns:
        JSON with inflation proxies and real rate estimates.
    """
    return _mcp_inflation(country=country)


@function_tool
def get_credit_spreads() -> str:
    """Get credit spread proxies as a risk appetite indicator.

    Compares high-yield bonds (HYG) vs investment-grade (LQD) and treasuries.
    Widening spreads = risk-off/stress. Tightening = risk-on/complacency.

    Returns:
        JSON with HY vs IG spread changes, risk signal classification.
    """
    return _mcp_credit()


@function_tool
def get_treasury_curve() -> str:
    """Get detailed treasury yield curve shape with real rate estimates.

    Provides short/mid/long rates, curve slope, term premium signal,
    and inflation expectations via TIPS comparison. Essential for
    identifying macro regime shifts.

    Returns:
        JSON with curve shape, slope, real rate proxy, term premium.
    """
    return _mcp_curve()
