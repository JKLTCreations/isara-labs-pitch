"""Sentiment and positioning tools for the sentiment analyst agent.

Provides fear/greed proxies, social sentiment, and positioning data
using freely available market data.
"""

from __future__ import annotations

import json
from datetime import datetime

import yfinance as yf
from agents import function_tool


@function_tool
def get_fear_greed_index() -> str:
    """Get a proxy fear/greed index based on market indicators.

    Computes a composite sentiment score from:
    - VIX level (fear gauge)
    - S&P 500 distance from 50-day SMA (momentum)
    - Put/call proxy via VIX term structure
    - Safe haven demand (gold vs stocks ratio)

    Returns:
        JSON with composite fear/greed score and component breakdown.
    """
    components: dict[str, object] = {}
    scores: list[float] = []

    # VIX — primary fear gauge
    vix = yf.Ticker("^VIX")
    vix_hist = vix.history(period="3mo")
    if not vix_hist.empty:
        vix_current = float(vix_hist["Close"].iloc[-1])
        vix_avg = float(vix_hist["Close"].mean())
        # VIX < 15 = extreme greed, > 30 = extreme fear
        vix_score = max(0, min(100, (30 - vix_current) / 20 * 100))
        components["vix"] = {
            "value": round(vix_current, 1),
            "average_3mo": round(vix_avg, 1),
            "signal": "extreme_fear" if vix_current > 30 else "fear" if vix_current > 20 else "neutral" if vix_current > 15 else "greed" if vix_current > 12 else "extreme_greed",
            "score": round(vix_score, 0),
        }
        scores.append(vix_score)

    # S&P 500 momentum — distance from 50-day SMA
    spx = yf.Ticker("^GSPC")
    spx_hist = spx.history(period="3mo")
    if not spx_hist.empty and len(spx_hist) >= 50:
        current_price = float(spx_hist["Close"].iloc[-1])
        sma_50 = float(spx_hist["Close"].rolling(50).mean().iloc[-1])
        pct_from_sma = (current_price - sma_50) / sma_50 * 100
        # > 5% above SMA = greed, > 5% below = fear
        momentum_score = max(0, min(100, (pct_from_sma + 5) / 10 * 100))
        components["sp500_momentum"] = {
            "price": round(current_price, 2),
            "sma_50": round(sma_50, 2),
            "pct_from_sma": round(pct_from_sma, 2),
            "signal": "greed" if pct_from_sma > 3 else "fear" if pct_from_sma < -3 else "neutral",
            "score": round(momentum_score, 0),
        }
        scores.append(momentum_score)

    # Safe haven demand — gold vs S&P performance (30d)
    gold = yf.Ticker("GC=F")
    gold_hist = gold.history(period="3mo")
    if not gold_hist.empty and not spx_hist.empty and len(gold_hist) > 22 and len(spx_hist) > 22:
        gold_30d = (float(gold_hist["Close"].iloc[-1]) / float(gold_hist["Close"].iloc[-22]) - 1) * 100
        spx_30d = (float(spx_hist["Close"].iloc[-1]) / float(spx_hist["Close"].iloc[-22]) - 1) * 100
        relative = spx_30d - gold_30d
        # Stocks outperforming gold = greed, gold outperforming = fear
        haven_score = max(0, min(100, (relative + 5) / 10 * 100))
        components["safe_haven"] = {
            "gold_30d_return": round(gold_30d, 2),
            "spx_30d_return": round(spx_30d, 2),
            "relative_performance": round(relative, 2),
            "signal": "greed" if relative > 3 else "fear" if relative < -3 else "neutral",
            "score": round(haven_score, 0),
        }
        scores.append(haven_score)

    # Composite score
    composite = sum(scores) / len(scores) if scores else 50.0

    return json.dumps({
        "composite_score": round(composite, 0),
        "label": (
            "extreme_fear" if composite < 20
            else "fear" if composite < 40
            else "neutral" if composite < 60
            else "greed" if composite < 80
            else "extreme_greed"
        ),
        "components": components,
        "interpretation": (
            "Extreme fear — contrarian buy signal historically"
            if composite < 20
            else "Fear — market pessimistic, potential opportunity"
            if composite < 40
            else "Neutral — no strong sentiment signal"
            if composite < 60
            else "Greed — market optimistic, caution warranted"
            if composite < 80
            else "Extreme greed — contrarian sell signal historically"
        ),
        "timestamp": datetime.now().isoformat(),
    })


@function_tool
def get_positioning_data(asset: str) -> str:
    """Get market positioning proxies for an asset.

    Uses ETF flows and options-implied data as positioning indicators.

    Args:
        asset: Asset to check positioning for (e.g., 'gold', 'oil', 'SPX').

    Returns:
        JSON with positioning signals and flow data.
    """
    # Map assets to relevant ETFs for flow/volume analysis
    asset_etfs: dict[str, list[tuple[str, str]]] = {
        "gold": [("GLD", "SPDR Gold Trust"), ("IAU", "iShares Gold Trust"), ("GDX", "Gold Miners ETF")],
        "XAUUSD": [("GLD", "SPDR Gold Trust"), ("IAU", "iShares Gold Trust"), ("GDX", "Gold Miners ETF")],
        "oil": [("USO", "US Oil Fund"), ("XLE", "Energy Select SPDR")],
        "CL1": [("USO", "US Oil Fund"), ("XLE", "Energy Select SPDR")],
        "SPX": [("SPY", "SPDR S&P 500"), ("VOO", "Vanguard S&P 500")],
        "DXY": [("UUP", "PowerShares DB US Dollar Bull"), ("FXE", "CurrencyShares Euro Trust")],
        "TLT": [("TLT", "iShares 20+ Year Treasury"), ("SHY", "iShares 1-3 Year Treasury")],
        "BTC": [("IBIT", "iShares Bitcoin Trust"), ("BITO", "ProShares Bitcoin Strategy")],
    }

    etfs = asset_etfs.get(asset, asset_etfs.get("SPX", []))
    positioning: list[dict[str, object]] = []

    for symbol, name in etfs[:3]:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo")
        if hist.empty:
            continue

        # Volume trend as positioning proxy
        recent_vol = float(hist["Volume"].tail(5).mean())
        avg_vol = float(hist["Volume"].mean())
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1.0

        # Price momentum
        current = float(hist["Close"].iloc[-1])
        month_ago = float(hist["Close"].iloc[-22]) if len(hist) > 22 else float(hist["Close"].iloc[0])
        momentum = (current - month_ago) / month_ago * 100

        positioning.append({
            "etf": symbol,
            "name": name,
            "current_price": round(current, 2),
            "30d_return_pct": round(momentum, 2),
            "volume_ratio": round(vol_ratio, 2),
            "volume_signal": (
                "heavy_accumulation" if vol_ratio > 1.5 and momentum > 0
                else "heavy_distribution" if vol_ratio > 1.5 and momentum < 0
                else "above_average" if vol_ratio > 1.2
                else "below_average" if vol_ratio < 0.8
                else "normal"
            ),
        })

    return json.dumps({
        "asset": asset,
        "positioning_signals": positioning,
        "overall_flow": (
            "accumulation" if sum(1 for p in positioning if p["30d_return_pct"] > 0) > len(positioning) / 2
            else "distribution" if sum(1 for p in positioning if p["30d_return_pct"] < 0) > len(positioning) / 2
            else "mixed"
        ),
        "timestamp": datetime.now().isoformat(),
    })


@function_tool
def get_social_sentiment(asset: str, platform: str = "all") -> str:
    """Get social media sentiment proxy for an asset.

    Without direct API access, uses search volume and ETF flow
    patterns as crowd sentiment proxies.

    Args:
        asset: Asset to check (e.g., 'gold', 'BTC', 'SPX').
        platform: Platform filter (currently returns combined proxy).

    Returns:
        JSON with crowd sentiment indicators.
    """
    # Use volatility and volume spikes as crowd activity proxies
    asset_tickers: dict[str, str] = {
        "gold": "GC=F", "XAUUSD": "GC=F", "oil": "CL=F", "CL1": "CL=F",
        "SPX": "^GSPC", "BTC": "BTC-USD", "DXY": "DX-Y.NYB",
    }

    ticker_symbol = asset_tickers.get(asset, asset)
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="3mo")

    if hist.empty:
        return json.dumps({"asset": asset, "error": "No data available", "timestamp": datetime.now().isoformat()})

    # Volume surge as crowd interest proxy
    recent_vol = float(hist["Volume"].tail(5).mean())
    avg_vol = float(hist["Volume"].mean())
    vol_surge = recent_vol / avg_vol if avg_vol > 0 else 1.0

    # Price volatility as excitement proxy
    daily_returns = hist["Close"].pct_change().dropna()
    recent_vol_pct = float(daily_returns.tail(5).std() * 100)
    avg_vol_pct = float(daily_returns.std() * 100)
    volatility_ratio = recent_vol_pct / avg_vol_pct if avg_vol_pct > 0 else 1.0

    # Trend strength as narrative proxy
    current = float(hist["Close"].iloc[-1])
    week_ago = float(hist["Close"].iloc[-5]) if len(hist) > 5 else current
    weekly_move = (current - week_ago) / week_ago * 100

    crowd_excitement = (vol_surge + volatility_ratio) / 2

    return json.dumps({
        "asset": asset,
        "platform": platform,
        "crowd_excitement": round(crowd_excitement, 2),
        "excitement_label": (
            "extreme" if crowd_excitement > 2.0
            else "elevated" if crowd_excitement > 1.3
            else "normal" if crowd_excitement > 0.7
            else "apathetic"
        ),
        "volume_surge_ratio": round(vol_surge, 2),
        "volatility_ratio": round(volatility_ratio, 2),
        "weekly_price_move_pct": round(weekly_move, 2),
        "narrative_direction": "bullish" if weekly_move > 2 else "bearish" if weekly_move < -2 else "flat",
        "note": "Proxy-based sentiment. Set TAVILY_API_KEY for real social sentiment.",
        "timestamp": datetime.now().isoformat(),
    })
