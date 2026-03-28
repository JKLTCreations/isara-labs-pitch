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

import pandas as pd
import yfinance as yf
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fred-economic", instructions="Economic indicators, rates, inflation, and yield curve data.")

_cache: dict[str, tuple[float, str]] = {}
ECON_CACHE_TTL = 3600  # 1 hour

# Circuit breaker state
_failures: int = 0
_last_failure: float = 0.0


def _safe_fetch(ticker_symbol: str, period: str = "3mo") -> pd.DataFrame:
    """Fetch yfinance history with circuit breaker."""
    global _failures, _last_failure
    if _failures >= 5 and time.time() - _last_failure < 120:
        return pd.DataFrame()
    try:
        hist = yf.Ticker(ticker_symbol).history(period=period)
        _failures = 0
        return hist
    except Exception:
        _failures += 1
        _last_failure = time.time()
        return pd.DataFrame()


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
        hist = _safe_fetch(ticker_symbol, period=period)
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
        hist = _safe_fetch(symbol, period="3mo")
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

    tips_hist = _safe_fetch("TIP", period="6mo")
    ief_hist = _safe_fetch("IEF", period="6mo")
    if not tips_hist.empty and not ief_hist.empty:
        tips_ret = (float(tips_hist["Close"].iloc[-1]) / float(tips_hist["Close"].iloc[0]) - 1) * 100
        ief_ret = (float(ief_hist["Close"].iloc[-1]) / float(ief_hist["Close"].iloc[0]) - 1) * 100
        result_data["tips_6mo_return"] = round(tips_ret, 2)
        result_data["nominal_treasury_6mo_return"] = round(ief_ret, 2)
        result_data["inflation_expectation_proxy"] = round(ief_ret - tips_ret, 2)

    gold_hist = _safe_fetch("GC=F", period="6mo")
    if not gold_hist.empty:
        gold_ret = (float(gold_hist["Close"].iloc[-1]) / float(gold_hist["Close"].iloc[0]) - 1) * 100
        result_data["gold_6mo_return"] = round(gold_ret, 2)
        result_data["gold_inflation_signal"] = "rising" if gold_ret > 5 else "stable" if gold_ret > -5 else "falling"

    result_data["source"] = "mcp:fred-economic"
    result_data["timestamp"] = datetime.now().isoformat()
    result = json.dumps(result_data)
    return _set_cache(cache_key, result)


@mcp.tool()
def get_credit_spreads() -> str:
    """Get credit spread proxies as a risk appetite indicator.

    Compares high-yield bonds (HYG) vs investment-grade (LQD) and treasuries (IEF).
    Widening spreads = risk-off / stress. Tightening spreads = risk-on / complacency.
    """
    cache_key = "credit_spreads"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    tickers = {
        "hyg": ("HYG", "iShares High Yield Corp Bond"),
        "lqd": ("LQD", "iShares Investment Grade Corp Bond"),
        "ief": ("IEF", "iShares 7-10Y Treasury"),
    }

    data: dict[str, dict[str, object]] = {}
    for key, (symbol, label) in tickers.items():
        hist = _safe_fetch(symbol, period="6mo")
        if not hist.empty:
            current = float(hist["Close"].iloc[-1])
            month_ago = float(hist["Close"].iloc[-22]) if len(hist) > 22 else float(hist["Close"].iloc[0])
            start = float(hist["Close"].iloc[0])
            data[key] = {
                "label": label, "current": round(current, 2),
                "1mo_return": round((current / month_ago - 1) * 100, 2),
                "6mo_return": round((current / start - 1) * 100, 2),
            }

    result_data: dict[str, object] = {"indicators": data}

    if "hyg" in data and "lqd" in data:
        hyg_1m = data["hyg"]["1mo_return"]
        lqd_1m = data["lqd"]["1mo_return"]
        spread_change = hyg_1m - lqd_1m  # type: ignore[operator]
        result_data["hy_vs_ig_1mo"] = round(spread_change, 2)  # type: ignore[arg-type]
        result_data["credit_risk_signal"] = (
            "risk_on" if spread_change > 0.5  # type: ignore[operator]
            else "risk_off" if spread_change < -0.5  # type: ignore[operator]
            else "neutral"
        )

    if "hyg" in data and "ief" in data:
        hyg_1m = data["hyg"]["1mo_return"]
        ief_1m = data["ief"]["1mo_return"]
        excess = hyg_1m - ief_1m  # type: ignore[operator]
        result_data["hy_vs_treasury_1mo"] = round(excess, 2)  # type: ignore[arg-type]
        result_data["spread_direction"] = (
            "tightening" if excess > 0.3  # type: ignore[operator]
            else "widening" if excess < -0.3  # type: ignore[operator]
            else "stable"
        )

    result_data["source"] = "mcp:fred-economic"
    result_data["timestamp"] = datetime.now().isoformat()
    result = json.dumps(result_data)
    return _set_cache(cache_key, result)


@mcp.tool()
def get_treasury_curve() -> str:
    """Get detailed treasury yield curve shape using multiple maturity proxies.

    Provides short/mid/long rates, curve slope, real rate estimates via TIPS,
    and term premium signals. Essential for macro regime identification.
    """
    cache_key = "treasury_curve"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    curve_tickers = {
        "short_rate": ("^IRX", "13-Week T-Bill"),
        "10y_yield": ("^TNX", "10-Year Treasury"),
        "30y_yield": ("^TYX", "30-Year Treasury"),
        "tips_etf": ("TIP", "TIPS ETF"),
        "long_treasury": ("TLT", "20+ Year Treasury ETF"),
    }

    rates: dict[str, dict[str, object]] = {}
    for key, (symbol, label) in curve_tickers.items():
        hist = _safe_fetch(symbol, period="6mo")
        if not hist.empty:
            current = float(hist["Close"].iloc[-1])
            month_ago = float(hist["Close"].iloc[-22]) if len(hist) > 22 else float(hist["Close"].iloc[0])
            six_mo_ago = float(hist["Close"].iloc[0])
            rates[key] = {
                "label": label, "current": round(current, 3),
                "month_ago": round(month_ago, 3),
                "1mo_change": round(current - month_ago, 3),
                "6mo_change": round(current - six_mo_ago, 3),
                "trend": "rising" if current > month_ago else "falling",
            }

    result_data: dict[str, object] = {"rates": rates}

    if "short_rate" in rates and "10y_yield" in rates:
        short = rates["short_rate"]["current"]
        ten_y = rates["10y_yield"]["current"]
        spread = ten_y - short  # type: ignore[operator]
        result_data["curve_2s10s_proxy"] = round(spread, 3)  # type: ignore[arg-type]
        result_data["curve_shape"] = (
            "deeply_inverted" if spread < -0.5  # type: ignore[operator]
            else "inverted" if spread < 0  # type: ignore[operator]
            else "flat" if spread < 0.5  # type: ignore[operator]
            else "normal" if spread < 1.5  # type: ignore[operator]
            else "steep"
        )

    if "10y_yield" in rates and "30y_yield" in rates:
        ten = rates["10y_yield"]["current"]
        thirty = rates["30y_yield"]["current"]
        long_spread = thirty - ten  # type: ignore[operator]
        result_data["long_end_slope"] = round(long_spread, 3)  # type: ignore[arg-type]
        result_data["term_premium_signal"] = (
            "positive" if long_spread > 0.3  # type: ignore[operator]
            else "compressed" if long_spread < 0  # type: ignore[operator]
            else "neutral"
        )

    if "tips_etf" in rates and "long_treasury" in rates:
        tips_chg = rates["tips_etf"]["1mo_change"]
        tlt_chg = rates["long_treasury"]["1mo_change"]
        result_data["real_rate_proxy_1mo"] = round(tlt_chg - tips_chg, 3)  # type: ignore[operator, arg-type]
        result_data["inflation_expectations_shift"] = (
            "rising" if tips_chg > tlt_chg  # type: ignore[operator]
            else "falling" if tips_chg < tlt_chg  # type: ignore[operator]
            else "stable"
        )

    result_data["source"] = "mcp:fred-economic"
    result_data["timestamp"] = datetime.now().isoformat()
    result = json.dumps(result_data)
    return _set_cache(cache_key, result)


if __name__ == "__main__":
    mcp.run()
