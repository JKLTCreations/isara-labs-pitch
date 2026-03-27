"""MCP server for economic indicators (FRED data).

Exposes GDP, CPI, interest rates, inflation, and yield curve data.
Built-in 1-hour cache for economic data.

Run standalone:
    python -m src.mcp.fred_server
"""

from __future__ import annotations

import json
import time
from datetime import datetime

import yfinance as yf
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fred-economic", instructions="Economic indicators, rates, inflation, and yield curve data.")

_cache: dict[str, tuple[float, str]] = {}
ECON_CACHE_TTL = 3600  # 1 hour


def _get_cached(key: str) -> str | None:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < ECON_CACHE_TTL:
            return data
    return None


def _set_cache(key: str, data: str) -> str:
    _cache[key] = (time.time(), data)
    return data


# FRED series to yfinance proxies
FRED_YF_MAP: dict[str, tuple[str, str]] = {
    "DGS10": ("^TNX", "10-Year Treasury Yield"),
    "DGS2": ("^IRX", "13-Week T-Bill Rate"),
    "DCOILWTICO": ("CL=F", "WTI Crude Oil"),
    "GOLDAMGBD228NLBM": ("GC=F", "Gold Price"),
    "DTWEXBGS": ("DX-Y.NYB", "US Dollar Index"),
}

FRED_DESCRIPTIONS: dict[str, str] = {
    "GDP": "Gross Domestic Product",
    "CPIAUCSL": "Consumer Price Index (All Urban)",
    "UNRATE": "Unemployment Rate",
    "FEDFUNDS": "Federal Funds Rate",
    "DGS10": "10-Year Treasury Yield",
    "DGS2": "2-Year Treasury Yield",
    "T10Y2Y": "10Y-2Y Treasury Spread",
    "DCOILWTICO": "WTI Crude Oil Price",
    "GOLDAMGBD228NLBM": "Gold Fixing Price",
    "DTWEXBGS": "Trade Weighted USD Index",
    "M2SL": "M2 Money Supply",
    "PCEPI": "PCE Price Index",
}


@mcp.tool()
def get_series(series_id: str, period: str = "1y") -> str:
    """Fetch a FRED economic data series.

    Commonly used series: GDP, CPIAUCSL, UNRATE, FEDFUNDS, DGS10, DGS2,
    T10Y2Y, DCOILWTICO, GOLDAMGBD228NLBM, DTWEXBGS, M2SL, PCEPI.

    Args:
        series_id: FRED series identifier.
        period: Lookback period (6mo, 1y, 2y, 5y).
    """
    cache_key = f"fred:{series_id}:{period}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    proxy = FRED_YF_MAP.get(series_id)
    description = FRED_DESCRIPTIONS.get(series_id, series_id)

    if proxy:
        ticker_symbol, label = proxy
        hist = yf.Ticker(ticker_symbol).history(period=period)
        if hist.empty:
            return json.dumps({"error": f"No data for {series_id} via {ticker_symbol}"})

        current = float(hist["Close"].iloc[-1])
        prev_month = float(hist["Close"].iloc[-22]) if len(hist) > 22 else float(hist["Close"].iloc[0])
        period_start = float(hist["Close"].iloc[0])

        recent = []
        for date, row in hist.tail(10).iterrows():
            recent.append({"date": date.strftime("%Y-%m-%d"), "value": round(float(row["Close"]), 4)})

        result = json.dumps({
            "series_id": series_id, "description": description,
            "source": f"mcp:fred-economic (proxy: {ticker_symbol})",
            "current_value": round(current, 4),
            "month_ago_value": round(prev_month, 4),
            "monthly_change": round(current - prev_month, 4),
            "period_start_value": round(period_start, 4),
            "period_change": round(current - period_start, 4),
            "recent_values": recent,
            "cached": False,
            "timestamp": datetime.now().isoformat(),
        })
        return _set_cache(cache_key, result)

    return json.dumps({
        "series_id": series_id, "description": description,
        "error": "FRED API key not configured. Set FRED_API_KEY for full access.",
        "available_proxied": list(FRED_YF_MAP.keys()),
        "timestamp": datetime.now().isoformat(),
    })


@mcp.tool()
def get_rate_expectations(currency: str = "USD") -> str:
    """Get interest rate environment, yield curve shape, and rate trends.

    Args:
        currency: Currency code (currently USD only).
    """
    cache_key = f"rates:{currency}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    if currency != "USD":
        return json.dumps({"error": f"Only USD supported, got {currency}"})

    tickers = {
        "us_10y": ("^TNX", "10-Year Treasury Yield"),
        "us_2y": ("^IRX", "13-Week T-Bill Rate"),
        "dollar_index": ("DX-Y.NYB", "US Dollar Index"),
    }

    rates: dict[str, object] = {"currency": currency}
    for key, (symbol, label) in tickers.items():
        hist = yf.Ticker(symbol).history(period="3mo")
        if not hist.empty:
            current = float(hist["Close"].iloc[-1])
            month_ago = float(hist["Close"].iloc[-22]) if len(hist) > 22 else float(hist["Close"].iloc[0])
            rates[key] = {
                "label": label, "current": round(current, 3),
                "month_ago": round(month_ago, 3),
                "change": round(current - month_ago, 3),
                "trend": "rising" if current > month_ago else "falling",
            }

    if "us_10y" in rates and "us_2y" in rates:
        ten_y = rates["us_10y"]["current"]  # type: ignore[index]
        two_y = rates["us_2y"]["current"]  # type: ignore[index]
        spread = ten_y - two_y
        rates["yield_curve"] = {
            "spread_10y_2y": round(spread, 3),
            "shape": "inverted" if spread < 0 else "flat" if spread < 0.5 else "normal",
            "recession_signal": spread < 0,
        }

    rates["source"] = "mcp:fred-economic"
    rates["timestamp"] = datetime.now().isoformat()
    result = json.dumps(rates)
    return _set_cache(cache_key, result)


@mcp.tool()
def get_inflation_breakdown(country: str = "US") -> str:
    """Get inflation proxies: TIPS vs nominal treasuries, gold as hedge signal.

    Args:
        country: Country code (currently US only).
    """
    cache_key = f"inflation:{country}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    if country != "US":
        return json.dumps({"error": f"Only US supported, got {country}"})

    result_data: dict[str, object] = {"country": country}

    tips_hist = yf.Ticker("TIP").history(period="6mo")
    ief_hist = yf.Ticker("IEF").history(period="6mo")
    if not tips_hist.empty and not ief_hist.empty:
        tips_ret = (float(tips_hist["Close"].iloc[-1]) / float(tips_hist["Close"].iloc[0]) - 1) * 100
        ief_ret = (float(ief_hist["Close"].iloc[-1]) / float(ief_hist["Close"].iloc[0]) - 1) * 100
        result_data["tips_6mo_return"] = round(tips_ret, 2)
        result_data["nominal_treasury_6mo_return"] = round(ief_ret, 2)
        result_data["inflation_expectation_proxy"] = round(ief_ret - tips_ret, 2)

    gold_hist = yf.Ticker("GC=F").history(period="6mo")
    if not gold_hist.empty:
        gold_ret = (float(gold_hist["Close"].iloc[-1]) / float(gold_hist["Close"].iloc[0]) - 1) * 100
        result_data["gold_6mo_return"] = round(gold_ret, 2)
        result_data["gold_inflation_signal"] = "rising" if gold_ret > 5 else "stable" if gold_ret > -5 else "falling"

    result_data["source"] = "mcp:fred-economic"
    result_data["timestamp"] = datetime.now().isoformat()
    result = json.dumps(result_data)
    return _set_cache(cache_key, result)


if __name__ == "__main__":
    mcp.run()
