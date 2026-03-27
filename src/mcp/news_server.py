"""MCP server for news and sentiment data.

Exposes news search, sentiment scoring, fear/greed, and positioning.
Built-in 15-minute cache for news data.

Run standalone:
    python -m src.mcp.news_server
"""

from __future__ import annotations

import json
import time
from datetime import datetime

import pandas as pd
import yfinance as yf
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("news-sentiment", instructions="News search, sentiment analysis, fear/greed index, and positioning data.")

_cache: dict[str, tuple[float, str]] = {}
NEWS_CACHE_TTL = 900  # 15 minutes

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
        if time.time() - ts < NEWS_CACHE_TTL:
            return data
    return None


def _set_cache(key: str, data: str) -> str:
    _cache[key] = (time.time(), data)
    return data


QUERY_TICKER_MAP: dict[str, list[str]] = {
    "gold": ["GC=F", "GLD"], "oil": ["CL=F", "USO"],
    "treasury": ["TLT", "IEF"], "dollar": ["DX-Y.NYB", "UUP"],
    "sp500": ["^GSPC", "SPY"], "inflation": ["TIP", "GC=F"],
    "china": ["FXI", "KWEB"], "bitcoin": ["BTC-USD"],
}

ASSET_TICKERS: dict[str, str] = {
    "gold": "GC=F", "XAUUSD": "GC=F", "oil": "CL=F", "CL1": "CL=F",
    "SPX": "^GSPC", "DXY": "DX-Y.NYB", "BTC": "BTC-USD", "TLT": "TLT",
}


@mcp.tool()
def search_news(query: str, region: str = "global", days_back: int = 7) -> str:
    """Search recent news articles relevant to a forecast.

    Args:
        query: Search query (e.g. 'gold prices', 'OPEC production').
        region: Geographic focus (global, US, EU, Asia, Middle East).
        days_back: How far back to search (1-30).
    """
    cache_key = f"news:{query}:{region}:{days_back}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    tickers_to_check: list[str] = []
    for keyword, tlist in QUERY_TICKER_MAP.items():
        if keyword.lower() in query.lower():
            tickers_to_check.extend(tlist)
    if not tickers_to_check:
        tickers_to_check = ["^GSPC", "GC=F", "CL=F"]

    articles: list[dict[str, str]] = []
    seen: set[str] = set()

    for symbol in tickers_to_check[:3]:
        try:
            news = yf.Ticker(symbol).news or []
            for item in news[:5]:
                content = item.get("content", {})
                title = content.get("title", "")
                if title and title not in seen:
                    seen.add(title)
                    articles.append({
                        "title": title,
                        "summary": content.get("summary", ""),
                        "source": content.get("provider", {}).get("displayName", "Unknown"),
                        "published": content.get("pubDate", ""),
                        "ticker_context": symbol,
                    })
        except Exception:
            continue

    result = json.dumps({
        "query": query, "region": region, "days_back": days_back,
        "article_count": len(articles), "articles": articles[:10],
        "source": "mcp:news-sentiment",
        "timestamp": datetime.now().isoformat(),
    })
    return _set_cache(cache_key, result)


@mcp.tool()
def get_sentiment_score(asset: str, days_back: int = 7) -> str:
    """Get aggregated news sentiment for an asset.

    Args:
        asset: Asset name (e.g. gold, oil, SPX).
        days_back: Days of news to analyze.
    """
    cache_key = f"sentiment:{asset}:{days_back}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    ticker_symbol = ASSET_TICKERS.get(asset, asset)

    try:
        news = yf.Ticker(ticker_symbol).news or []
    except Exception:
        news = []

    if not news:
        return json.dumps({"asset": asset, "sentiment": "unknown", "article_count": 0,
                          "timestamp": datetime.now().isoformat()})

    pos_kw = {"surge", "rally", "gain", "rise", "jump", "bullish", "record", "strong", "soar", "up"}
    neg_kw = {"drop", "fall", "crash", "decline", "plunge", "bearish", "weak", "sink", "loss", "down"}

    pos = neg = 0
    titles: list[str] = []
    for item in news[:15]:
        content = item.get("content", {})
        title = content.get("title", "")
        titles.append(title)
        tl = title.lower()
        pos += sum(1 for kw in pos_kw if kw in tl)
        neg += sum(1 for kw in neg_kw if kw in tl)

    total = pos + neg
    score = (pos - neg) / total if total > 0 else 0.0
    label = "positive" if score > 0.3 else "negative" if score < -0.3 else "mixed" if total > 0 else "neutral"

    result = json.dumps({
        "asset": asset, "sentiment": label, "sentiment_score": round(score, 2),
        "positive_signals": pos, "negative_signals": neg,
        "article_count": min(len(news), 15), "sample_headlines": titles[:5],
        "source": "mcp:news-sentiment",
        "timestamp": datetime.now().isoformat(),
    })
    return _set_cache(cache_key, result)


@mcp.tool()
def get_fear_greed_index() -> str:
    """Compute a proxy fear/greed index from VIX, S&P momentum, and safe haven demand."""
    cache_key = "fear_greed"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    components: dict[str, object] = {}
    scores: list[float] = []

    # VIX
    vix_hist = _safe_fetch("^VIX", period="3mo")
    if not vix_hist.empty:
        vix = float(vix_hist["Close"].iloc[-1])
        vix_score = max(0, min(100, (30 - vix) / 20 * 100))
        components["vix"] = {
            "value": round(vix, 1),
            "signal": "extreme_fear" if vix > 30 else "fear" if vix > 20 else "neutral" if vix > 15 else "greed",
            "score": round(vix_score, 0),
        }
        scores.append(vix_score)

    # SPX momentum
    spx_hist = _safe_fetch("^GSPC", period="3mo")
    if not spx_hist.empty and len(spx_hist) >= 50:
        px = float(spx_hist["Close"].iloc[-1])
        sma = float(spx_hist["Close"].rolling(50).mean().iloc[-1])
        pct = (px - sma) / sma * 100
        mom_score = max(0, min(100, (pct + 5) / 10 * 100))
        components["sp500_momentum"] = {
            "pct_from_sma50": round(pct, 2),
            "signal": "greed" if pct > 3 else "fear" if pct < -3 else "neutral",
            "score": round(mom_score, 0),
        }
        scores.append(mom_score)

    # Safe haven
    gold_hist = _safe_fetch("GC=F", period="3mo")
    if not gold_hist.empty and not spx_hist.empty and len(gold_hist) > 22 and len(spx_hist) > 22:
        g30 = (float(gold_hist["Close"].iloc[-1]) / float(gold_hist["Close"].iloc[-22]) - 1) * 100
        s30 = (float(spx_hist["Close"].iloc[-1]) / float(spx_hist["Close"].iloc[-22]) - 1) * 100
        rel = s30 - g30
        haven_score = max(0, min(100, (rel + 5) / 10 * 100))
        components["safe_haven"] = {
            "gold_30d": round(g30, 2), "spx_30d": round(s30, 2),
            "signal": "greed" if rel > 3 else "fear" if rel < -3 else "neutral",
            "score": round(haven_score, 0),
        }
        scores.append(haven_score)

    composite = sum(scores) / len(scores) if scores else 50.0

    result = json.dumps({
        "composite_score": round(composite, 0),
        "label": (
            "extreme_fear" if composite < 20 else "fear" if composite < 40
            else "neutral" if composite < 60 else "greed" if composite < 80 else "extreme_greed"
        ),
        "components": components,
        "source": "mcp:news-sentiment",
        "timestamp": datetime.now().isoformat(),
    })
    return _set_cache(cache_key, result)


@mcp.tool()
def get_positioning(asset: str) -> str:
    """Get market positioning proxies from ETF volume and flow patterns.

    Args:
        asset: Asset to check (e.g. gold, oil, SPX, BTC).
    """
    cache_key = f"positioning:{asset}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    asset_etfs: dict[str, list[tuple[str, str]]] = {
        "gold": [("GLD", "SPDR Gold"), ("IAU", "iShares Gold"), ("GDX", "Gold Miners")],
        "XAUUSD": [("GLD", "SPDR Gold"), ("IAU", "iShares Gold"), ("GDX", "Gold Miners")],
        "oil": [("USO", "US Oil Fund"), ("XLE", "Energy SPDR")],
        "CL1": [("USO", "US Oil Fund"), ("XLE", "Energy SPDR")],
        "SPX": [("SPY", "SPDR S&P 500"), ("VOO", "Vanguard S&P 500")],
        "BTC": [("IBIT", "iShares Bitcoin"), ("BITO", "ProShares Bitcoin")],
    }

    etfs = asset_etfs.get(asset, [("SPY", "SPDR S&P 500")])
    positions: list[dict[str, object]] = []

    for symbol, name in etfs[:3]:
        hist = _safe_fetch(symbol, period="3mo")
        if hist.empty:
            continue
        recent_vol = float(hist["Volume"].tail(5).mean())
        avg_vol = float(hist["Volume"].mean())
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1.0
        px = float(hist["Close"].iloc[-1])
        m_ago = float(hist["Close"].iloc[-22]) if len(hist) > 22 else float(hist["Close"].iloc[0])
        mom = (px - m_ago) / m_ago * 100

        positions.append({
            "etf": symbol, "name": name, "current_price": round(px, 2),
            "30d_return_pct": round(mom, 2), "volume_ratio": round(vol_ratio, 2),
            "volume_signal": (
                "heavy_accumulation" if vol_ratio > 1.5 and mom > 0
                else "heavy_distribution" if vol_ratio > 1.5 and mom < 0
                else "above_average" if vol_ratio > 1.2
                else "below_average" if vol_ratio < 0.8 else "normal"
            ),
        })

    result = json.dumps({
        "asset": asset, "positioning_signals": positions,
        "overall_flow": (
            "accumulation" if sum(1 for p in positions if p["30d_return_pct"] > 0) > len(positions) / 2
            else "distribution" if sum(1 for p in positions if p["30d_return_pct"] < 0) > len(positions) / 2
            else "mixed"
        ),
        "source": "mcp:news-sentiment",
        "timestamp": datetime.now().isoformat(),
    })
    return _set_cache(cache_key, result)


if __name__ == "__main__":
    mcp.run()
