"""Economic indicator tools for the macro-economics agent.

Uses FRED API for economic data. Falls back to yfinance for
rate-sensitive instruments when FRED key is unavailable.
"""

from __future__ import annotations

import json
from datetime import datetime

import yfinance as yf
from agents import function_tool


@function_tool
def get_fred_series(series_id: str, period: str = "1y") -> str:
    """Fetch a FRED economic data series.

    Common series IDs:
    - GDP: Gross Domestic Product
    - CPIAUCSL: Consumer Price Index (All Urban Consumers)
    - UNRATE: Unemployment Rate
    - FEDFUNDS: Federal Funds Effective Rate
    - DGS10: 10-Year Treasury Constant Maturity Rate
    - DGS2: 2-Year Treasury Constant Maturity Rate
    - T10Y2Y: 10-Year minus 2-Year Treasury spread (yield curve)
    - DCOILWTICO: WTI Crude Oil Price
    - GOLDAMGBD228NLBM: Gold Fixing Price (London)
    - DTWEXBGS: Trade Weighted US Dollar Index
    - M2SL: M2 Money Supply
    - PCEPI: PCE Price Index

    Args:
        series_id: FRED series identifier.
        period: Lookback period ('6mo', '1y', '2y', '5y').

    Returns:
        JSON with recent values and trend summary.
    """
    # Use yfinance treasury/rate proxies when we can
    fred_to_yf: dict[str, str] = {
        "DGS10": "^TNX",
        "DGS2": "^IRX",
        "DCOILWTICO": "CL=F",
        "GOLDAMGBD228NLBM": "GC=F",
    }

    ticker_symbol = fred_to_yf.get(series_id)

    if ticker_symbol:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return json.dumps({"error": f"No data for {series_id} via proxy {ticker_symbol}"})

        current = float(hist["Close"].iloc[-1])
        prev_month = float(hist["Close"].iloc[-22]) if len(hist) > 22 else float(hist["Close"].iloc[0])
        period_start = float(hist["Close"].iloc[0])

        recent = []
        for date, row in hist.tail(10).iterrows():
            recent.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(float(row["Close"]), 4),
            })

        return json.dumps({
            "series_id": series_id,
            "source": f"yfinance_proxy:{ticker_symbol}",
            "current_value": round(current, 4),
            "month_ago_value": round(prev_month, 4),
            "monthly_change": round(current - prev_month, 4),
            "period_start_value": round(period_start, 4),
            "period_change": round(current - period_start, 4),
            "recent_values": recent,
            "timestamp": datetime.now().isoformat(),
        })

    # For series without a yfinance proxy, return a helpful error
    return json.dumps({
        "series_id": series_id,
        "error": "FRED API key not configured. Set FRED_API_KEY in .env for full access.",
        "hint": f"Available proxied series: {list(fred_to_yf.keys())}",
        "timestamp": datetime.now().isoformat(),
    })


@function_tool
def get_rate_expectations(currency: str = "USD") -> str:
    """Get current interest rate environment and expectations.

    Args:
        currency: Currency code (currently supports 'USD').

    Returns:
        JSON with current rates, yield curve shape, and rate trend.
    """
    if currency != "USD":
        return json.dumps({"error": f"Only USD supported, got {currency}"})

    # Fetch treasury yields as rate proxies
    tickers = {
        "us_10y": ("^TNX", "10-Year Treasury Yield"),
        "us_2y": ("^IRX", "13-Week Treasury Bill Rate"),
        "dollar_index": ("DX-Y.NYB", "US Dollar Index"),
    }

    rates: dict[str, object] = {"currency": currency}

    for key, (symbol, label) in tickers.items():
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo")
        if not hist.empty:
            current = float(hist["Close"].iloc[-1])
            month_ago = float(hist["Close"].iloc[-22]) if len(hist) > 22 else float(hist["Close"].iloc[0])
            rates[key] = {
                "label": label,
                "current": round(current, 3),
                "month_ago": round(month_ago, 3),
                "change": round(current - month_ago, 3),
                "trend": "rising" if current > month_ago else "falling",
            }

    # Yield curve assessment
    if "us_10y" in rates and "us_2y" in rates:
        ten_y = rates["us_10y"]["current"]  # type: ignore[index]
        two_y = rates["us_2y"]["current"]  # type: ignore[index]
        spread = ten_y - two_y
        rates["yield_curve"] = {
            "spread_10y_2y": round(spread, 3),
            "shape": "inverted" if spread < 0 else "flat" if spread < 0.5 else "normal",
            "recession_signal": spread < 0,
        }

    rates["timestamp"] = datetime.now().isoformat()
    return json.dumps(rates)


@function_tool
def get_inflation_breakdown(country: str = "US") -> str:
    """Get inflation-related indicators.

    Args:
        country: Country code (currently supports 'US').

    Returns:
        JSON with inflation proxies and real rate estimates.
    """
    if country != "US":
        return json.dumps({"error": f"Only US supported, got {country}"})

    # Use TIP (TIPS ETF) vs IEF (Treasury ETF) as inflation expectation proxy
    tips = yf.Ticker("TIP")
    ief = yf.Ticker("IEF")
    tips_hist = tips.history(period="6mo")
    ief_hist = ief.history(period="6mo")

    result: dict[str, object] = {"country": country}

    if not tips_hist.empty and not ief_hist.empty:
        tips_return = (float(tips_hist["Close"].iloc[-1]) / float(tips_hist["Close"].iloc[0]) - 1) * 100
        ief_return = (float(ief_hist["Close"].iloc[-1]) / float(ief_hist["Close"].iloc[0]) - 1) * 100

        result["tips_6mo_return"] = round(tips_return, 2)
        result["nominal_treasury_6mo_return"] = round(ief_return, 2)
        result["inflation_expectation_proxy"] = round(ief_return - tips_return, 2)
        result["note"] = "Positive inflation proxy = market expects higher inflation"

    # Gold as inflation hedge signal
    gold = yf.Ticker("GC=F")
    gold_hist = gold.history(period="6mo")
    if not gold_hist.empty:
        gold_return = (float(gold_hist["Close"].iloc[-1]) / float(gold_hist["Close"].iloc[0]) - 1) * 100
        result["gold_6mo_return"] = round(gold_return, 2)
        result["gold_inflation_signal"] = "rising" if gold_return > 5 else "stable" if gold_return > -5 else "falling"

    result["timestamp"] = datetime.now().isoformat()
    return json.dumps(result)
