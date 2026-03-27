"""MCP server for market data.

Exposes price data, technical indicators, volatility, and correlations
via the Model Context Protocol. Built-in 1-minute cache for price data.

Run standalone:
    python -m src.mcp.market_server
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from functools import lru_cache

import yfinance as yf
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("market-data", instructions="Real-time market data, technicals, and volatility.")

# Simple TTL cache
_cache: dict[str, tuple[float, str]] = {}
PRICE_CACHE_TTL = 60  # 1 minute


def _get_cached(key: str, ttl: int = PRICE_CACHE_TTL) -> str | None:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < ttl:
            return data
    return None


def _set_cache(key: str, data: str) -> str:
    _cache[key] = (time.time(), data)
    return data


# Ticker mapping
ASSET_TICKER_MAP: dict[str, str] = {
    "XAUUSD": "GC=F", "gold": "GC=F", "XAGUSD": "SI=F", "silver": "SI=F",
    "CL1": "CL=F", "oil": "CL=F", "DXY": "DX-Y.NYB", "SPX": "^GSPC",
    "NDX": "^IXIC", "TLT": "TLT", "BTC": "BTC-USD",
}


def _resolve(asset: str) -> str:
    return ASSET_TICKER_MAP.get(asset, asset)


@mcp.tool()
def get_price_data(asset: str, horizon: str = "30d") -> str:
    """Fetch OHLCV price data for an asset with summary statistics.

    Args:
        asset: Asset identifier (e.g. XAUUSD, gold, CL1, SPX, BTC).
        horizon: Forecast horizon to size lookback (e.g. 7d, 30d, 90d).
    """
    cache_key = f"price:{asset}:{horizon}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    ticker_symbol = _resolve(asset)
    days = int(horizon.rstrip("d"))
    lookback = days * 3
    period = "1mo" if lookback <= 30 else "3mo" if lookback <= 90 else "6mo" if lookback <= 180 else "1y"

    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=period)

    if hist.empty:
        return json.dumps({"error": f"No data for {asset} ({ticker_symbol})"})

    current = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
    period_open = float(hist["Close"].iloc[0])

    recent = []
    for date, row in hist.tail(10).iterrows():
        recent.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })

    result = json.dumps({
        "asset": asset, "ticker": ticker_symbol,
        "current_price": round(current, 2),
        "daily_change_pct": round((current - prev) / prev * 100, 3),
        "period_change_pct": round((current - period_open) / period_open * 100, 3),
        "period_high": round(float(hist["High"].max()), 2),
        "period_low": round(float(hist["Low"].min()), 2),
        "avg_volume": int(hist["Volume"].mean()),
        "data_start": hist.index[0].strftime("%Y-%m-%d"),
        "data_end": hist.index[-1].strftime("%Y-%m-%d"),
        "recent_prices": recent,
        "source": "mcp:market-data",
        "cached": False,
        "timestamp": datetime.now().isoformat(),
    })
    return _set_cache(cache_key, result)


@mcp.tool()
def get_technical_indicators(asset: str, horizon: str = "30d") -> str:
    """Calculate RSI, moving averages, Bollinger bands, MACD, and trend for an asset.

    Args:
        asset: Asset identifier (e.g. XAUUSD, CL1, SPX).
        horizon: Forecast horizon (e.g. 30d, 90d).
    """
    cache_key = f"tech:{asset}:{horizon}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    ticker_symbol = _resolve(asset)
    hist = yf.Ticker(ticker_symbol).history(period="6mo")

    if hist.empty or len(hist) < 26:
        return json.dumps({"error": f"Insufficient data for {asset}"})

    close = hist["Close"]
    current = float(close.iloc[-1])

    # RSI 14
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss
    rsi = float((100.0 - (100.0 / (1.0 + rs))).iloc[-1])

    # MAs
    sma_20 = float(close.rolling(20).mean().iloc[-1])
    sma_50 = float(close.rolling(50).mean().iloc[-1])
    sma_200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None

    # Bollinger
    bb_std = float(close.rolling(20).std().iloc[-1])
    bb_upper = sma_20 + 2 * bb_std
    bb_lower = sma_20 - 2 * bb_std
    bb_pos = (current - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5

    # MACD
    ema_12 = float(close.ewm(span=12, adjust=False).mean().iloc[-1])
    ema_26 = float(close.ewm(span=26, adjust=False).mean().iloc[-1])
    macd_line = ema_12 - ema_26
    signal_s = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    macd_signal = float(signal_s.ewm(span=9, adjust=False).mean().iloc[-1])

    # Volatility
    vol_20d = float(close.pct_change().dropna().tail(20).std() * (252 ** 0.5) * 100)

    # Trend
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

    result = json.dumps({
        "asset": asset, "current_price": round(current, 2),
        "rsi_14": round(rsi, 1),
        "rsi_signal": "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral",
        "sma_20": round(sma_20, 2), "sma_50": round(sma_50, 2),
        "sma_200": round(sma_200, 2) if sma_200 else None,
        "price_vs_sma20": round((current - sma_20) / sma_20 * 100, 2),
        "price_vs_sma50": round((current - sma_50) / sma_50 * 100, 2),
        "bollinger_upper": round(bb_upper, 2), "bollinger_mid": round(sma_20, 2),
        "bollinger_lower": round(bb_lower, 2), "bollinger_position": round(bb_pos, 3),
        "macd_line": round(macd_line, 3), "macd_signal": round(macd_signal, 3),
        "macd_histogram": round(macd_line - macd_signal, 3),
        "macd_crossover": "bullish" if macd_line > macd_signal else "bearish",
        "volatility_20d_annualized": round(vol_20d, 2),
        "trend": trend,
        "source": "mcp:market-data",
        "timestamp": datetime.now().isoformat(),
    })
    return _set_cache(cache_key, result)


@mcp.tool()
def get_volatility(asset: str) -> str:
    """Get historical volatility metrics for an asset.

    Args:
        asset: Asset identifier (e.g. XAUUSD, SPX, BTC).
    """
    cache_key = f"vol:{asset}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    ticker_symbol = _resolve(asset)
    hist = yf.Ticker(ticker_symbol).history(period="1y")

    if hist.empty or len(hist) < 30:
        return json.dumps({"error": f"Insufficient data for {asset}"})

    returns = hist["Close"].pct_change().dropna()
    vol_5d = float(returns.tail(5).std() * (252 ** 0.5) * 100)
    vol_20d = float(returns.tail(20).std() * (252 ** 0.5) * 100)
    vol_60d = float(returns.tail(60).std() * (252 ** 0.5) * 100)
    vol_252d = float(returns.std() * (252 ** 0.5) * 100)

    vol_ratio = vol_5d / vol_60d if vol_60d > 0 else 1.0

    result = json.dumps({
        "asset": asset,
        "vol_5d_annualized": round(vol_5d, 2),
        "vol_20d_annualized": round(vol_20d, 2),
        "vol_60d_annualized": round(vol_60d, 2),
        "vol_1y_annualized": round(vol_252d, 2),
        "vol_regime": (
            "elevated" if vol_ratio > 1.5 else "compressed" if vol_ratio < 0.6 else "normal"
        ),
        "vol_ratio_5d_60d": round(vol_ratio, 2),
        "max_daily_loss_1y": round(float(returns.min() * 100), 2),
        "max_daily_gain_1y": round(float(returns.max() * 100), 2),
        "source": "mcp:market-data",
        "timestamp": datetime.now().isoformat(),
    })
    return _set_cache(cache_key, result)


@mcp.tool()
def get_correlation_matrix(assets: str, period: str = "3mo") -> str:
    """Compute correlation matrix between multiple assets.

    Args:
        assets: Comma-separated asset list (e.g. 'XAUUSD,DXY,SPX,TLT').
        period: Lookback period (e.g. 1mo, 3mo, 6mo).
    """
    cache_key = f"corr:{assets}:{period}"
    cached = _get_cached(cache_key, ttl=300)  # 5 min cache for correlations
    if cached:
        return cached

    asset_list = [a.strip() for a in assets.split(",")]
    tickers = {a: _resolve(a) for a in asset_list}

    price_data = {}
    for asset_name, ticker_symbol in tickers.items():
        hist = yf.Ticker(ticker_symbol).history(period=period)
        if not hist.empty:
            price_data[asset_name] = hist["Close"]

    if len(price_data) < 2:
        return json.dumps({"error": "Need at least 2 assets with data"})

    import pandas as pd
    df = pd.DataFrame(price_data).pct_change().dropna()
    corr = df.corr()

    matrix: dict[str, dict[str, float]] = {}
    for col in corr.columns:
        matrix[col] = {row: round(float(corr.loc[row, col]), 3) for row in corr.index}

    result = json.dumps({
        "assets": asset_list,
        "period": period,
        "correlation_matrix": matrix,
        "notable_pairs": [
            {"pair": f"{a1}/{a2}", "correlation": matrix[a1][a2]}
            for i, a1 in enumerate(asset_list)
            for a2 in asset_list[i + 1:]
            if a1 in matrix and a2 in matrix.get(a1, {})
            and abs(matrix[a1][a2]) > 0.5
        ],
        "source": "mcp:market-data",
        "timestamp": datetime.now().isoformat(),
    })
    return _set_cache(cache_key, result)


if __name__ == "__main__":
    mcp.run()
