"""Market data tools for the quantitative analyst agent.

Uses yfinance for price data — free, no API key required.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import yfinance as yf
from agents import function_tool

# Mapping of common asset names to yfinance tickers
ASSET_TICKER_MAP: dict[str, str] = {
    "XAUUSD": "GC=F",       # Gold futures
    "gold": "GC=F",
    "XAGUSD": "SI=F",       # Silver futures
    "silver": "SI=F",
    "CL1": "CL=F",          # Crude oil futures
    "oil": "CL=F",
    "DXY": "DX-Y.NYB",      # US Dollar Index
    "SPX": "^GSPC",          # S&P 500
    "NDX": "^IXIC",          # Nasdaq
    "TLT": "TLT",           # 20+ Year Treasury ETF
    "BTC": "BTC-USD",       # Bitcoin
}


def _resolve_ticker(asset: str) -> str:
    return ASSET_TICKER_MAP.get(asset, asset)


def _period_from_horizon(horizon: str) -> str:
    """Convert a forecast horizon like '30d' to a yfinance lookback period."""
    days = int(horizon.rstrip("d"))
    # Look back 3x the horizon for context
    lookback = days * 3
    if lookback <= 30:
        return "1mo"
    elif lookback <= 90:
        return "3mo"
    elif lookback <= 180:
        return "6mo"
    else:
        return "1y"


@function_tool
def get_price_data(asset: str, horizon: str = "30d") -> str:
    """Fetch recent OHLCV price data for an asset.

    Args:
        asset: Asset identifier (e.g., 'XAUUSD', 'gold', 'CL1', 'SPX').
        horizon: Forecast horizon to determine lookback period (e.g., '30d', '90d').

    Returns:
        JSON string with price summary and recent data points.
    """
    ticker_symbol = _resolve_ticker(asset)
    period = _period_from_horizon(horizon)
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=period)

    if hist.empty:
        return json.dumps({"error": f"No data found for {asset} ({ticker_symbol})"})

    current_price = float(hist["Close"].iloc[-1])
    prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
    period_open = float(hist["Close"].iloc[0])

    # Recent daily data (last 10 trading days)
    recent = hist.tail(10)
    recent_data = []
    for date, row in recent.iterrows():
        recent_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })

    return json.dumps({
        "asset": asset,
        "ticker": ticker_symbol,
        "current_price": round(current_price, 2),
        "daily_change_pct": round((current_price - prev_close) / prev_close * 100, 3),
        "period_change_pct": round((current_price - period_open) / period_open * 100, 3),
        "period_high": round(float(hist["High"].max()), 2),
        "period_low": round(float(hist["Low"].min()), 2),
        "avg_volume": int(hist["Volume"].mean()),
        "data_start": hist.index[0].strftime("%Y-%m-%d"),
        "data_end": hist.index[-1].strftime("%Y-%m-%d"),
        "recent_prices": recent_data,
        "timestamp": datetime.now().isoformat(),
    })


@function_tool
def get_technical_indicators(asset: str, horizon: str = "30d") -> str:
    """Calculate key technical indicators for an asset.

    Args:
        asset: Asset identifier (e.g., 'XAUUSD', 'gold', 'CL1').
        horizon: Forecast horizon (e.g., '30d', '90d').

    Returns:
        JSON string with RSI, moving averages, Bollinger bands, and MACD.
    """
    ticker_symbol = _resolve_ticker(asset)
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="6mo")

    if hist.empty or len(hist) < 26:
        return json.dumps({"error": f"Insufficient data for {asset} ({ticker_symbol})"})

    close = hist["Close"]
    current = float(close.iloc[-1])

    # RSI (14-period)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi_value = float(rsi.iloc[-1])

    # Moving averages
    sma_20 = float(close.rolling(20).mean().iloc[-1])
    sma_50 = float(close.rolling(50).mean().iloc[-1])
    sma_200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None

    # Bollinger Bands (20-period, 2 std)
    bb_mid = sma_20
    bb_std = float(close.rolling(20).std().iloc[-1])
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    bb_position = (current - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5

    # MACD
    ema_12 = float(close.ewm(span=12, adjust=False).mean().iloc[-1])
    ema_26 = float(close.ewm(span=26, adjust=False).mean().iloc[-1])
    macd_line = ema_12 - ema_26
    signal_series = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    macd_signal = float(signal_series.ewm(span=9, adjust=False).mean().iloc[-1])
    macd_histogram = macd_line - macd_signal

    # Volatility (20-day annualized)
    daily_returns = close.pct_change().dropna()
    volatility_20d = float(daily_returns.tail(20).std() * (252 ** 0.5) * 100)

    # Trend detection
    if current > sma_20 > sma_50:
        trend = "strong_uptrend"
    elif current > sma_50:
        trend = "uptrend"
    elif current < sma_20 < sma_50:
        trend = "strong_downtrend"
    elif current < sma_50:
        trend = "downtrend"
    else:
        trend = "sideways"

    return json.dumps({
        "asset": asset,
        "current_price": round(current, 2),
        "rsi_14": round(rsi_value, 1),
        "rsi_signal": "overbought" if rsi_value > 70 else "oversold" if rsi_value < 30 else "neutral",
        "sma_20": round(sma_20, 2),
        "sma_50": round(sma_50, 2),
        "sma_200": round(sma_200, 2) if sma_200 else None,
        "price_vs_sma20": round((current - sma_20) / sma_20 * 100, 2),
        "price_vs_sma50": round((current - sma_50) / sma_50 * 100, 2),
        "bollinger_upper": round(bb_upper, 2),
        "bollinger_mid": round(bb_mid, 2),
        "bollinger_lower": round(bb_lower, 2),
        "bollinger_position": round(bb_position, 3),
        "macd_line": round(macd_line, 3),
        "macd_signal": round(macd_signal, 3),
        "macd_histogram": round(macd_histogram, 3),
        "macd_crossover": "bullish" if macd_histogram > 0 else "bearish",
        "volatility_20d_annualized": round(volatility_20d, 2),
        "trend": trend,
        "timestamp": datetime.now().isoformat(),
    })
