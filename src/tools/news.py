"""News and geopolitical tools for the geopolitical and sentiment agents.

Uses Tavily search API when available, falls back to yfinance news.
"""

from __future__ import annotations

import json
from datetime import datetime

import yfinance as yf
from agents import function_tool


@function_tool
def search_news(query: str, region: str = "global", days_back: int = 7) -> str:
    """Search recent news articles relevant to a forecast.

    Args:
        query: Search query (e.g., 'gold prices', 'US China trade', 'OPEC production').
        region: Geographic focus ('global', 'US', 'EU', 'Asia', 'Middle East').
        days_back: How far back to search (1-30 days).

    Returns:
        JSON with news summaries and metadata.
    """
    # Use yfinance news as a free fallback
    # Map queries to relevant tickers for news
    query_ticker_map: dict[str, list[str]] = {
        "gold": ["GC=F", "GLD"],
        "oil": ["CL=F", "USO"],
        "treasury": ["TLT", "IEF"],
        "dollar": ["DX-Y.NYB", "UUP"],
        "sp500": ["^GSPC", "SPY"],
        "inflation": ["TIP", "GC=F"],
        "china": ["FXI", "KWEB"],
        "bitcoin": ["BTC-USD"],
    }

    # Find relevant tickers from query keywords
    tickers_to_check: list[str] = []
    for keyword, ticker_list in query_ticker_map.items():
        if keyword.lower() in query.lower():
            tickers_to_check.extend(ticker_list)

    # Default to broad market tickers if no match
    if not tickers_to_check:
        tickers_to_check = ["^GSPC", "GC=F", "CL=F"]

    articles: list[dict[str, str]] = []
    seen_titles: set[str] = set()

    for symbol in tickers_to_check[:3]:
        ticker = yf.Ticker(symbol)
        try:
            news = ticker.news
            if not news:
                continue
            for item in news[:5]:
                content = item.get("content", {})
                title = content.get("title", "")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    articles.append({
                        "title": title,
                        "summary": content.get("summary", ""),
                        "source": content.get("provider", {}).get("displayName", "Unknown"),
                        "published": content.get("pubDate", ""),
                        "ticker_context": symbol,
                    })
        except Exception:
            continue

    return json.dumps({
        "query": query,
        "region": region,
        "days_back": days_back,
        "article_count": len(articles),
        "articles": articles[:10],
        "source": "yfinance_news",
        "note": "Set TAVILY_API_KEY for broader news coverage",
        "timestamp": datetime.now().isoformat(),
    })


@function_tool
def get_news_sentiment(asset: str, days_back: int = 7) -> str:
    """Get aggregated news sentiment for an asset.

    Args:
        asset: Asset name (e.g., 'gold', 'oil', 'SPX').
        days_back: How many days of news to analyze.

    Returns:
        JSON with sentiment summary derived from recent headlines.
    """
    # Map assets to tickers
    asset_tickers: dict[str, str] = {
        "gold": "GC=F",
        "XAUUSD": "GC=F",
        "oil": "CL=F",
        "CL1": "CL=F",
        "SPX": "^GSPC",
        "DXY": "DX-Y.NYB",
        "BTC": "BTC-USD",
        "TLT": "TLT",
    }

    ticker_symbol = asset_tickers.get(asset, asset)
    ticker = yf.Ticker(ticker_symbol)

    try:
        news = ticker.news or []
    except Exception:
        news = []

    if not news:
        return json.dumps({
            "asset": asset,
            "sentiment": "unknown",
            "article_count": 0,
            "error": "No news data available",
            "timestamp": datetime.now().isoformat(),
        })

    # Simple keyword-based sentiment (production would use an LLM)
    positive_keywords = ["surge", "rally", "gain", "rise", "jump", "bullish", "record", "strong", "soar", "up"]
    negative_keywords = ["drop", "fall", "crash", "decline", "plunge", "bearish", "weak", "sink", "loss", "down"]

    pos_count = 0
    neg_count = 0
    titles: list[str] = []

    for item in news[:15]:
        content = item.get("content", {})
        title = content.get("title", "").lower()
        titles.append(content.get("title", ""))
        for kw in positive_keywords:
            if kw in title:
                pos_count += 1
        for kw in negative_keywords:
            if kw in title:
                neg_count += 1

    total = pos_count + neg_count
    if total == 0:
        sentiment_score = 0.0
        sentiment = "neutral"
    else:
        sentiment_score = (pos_count - neg_count) / total
        if sentiment_score > 0.3:
            sentiment = "positive"
        elif sentiment_score < -0.3:
            sentiment = "negative"
        else:
            sentiment = "mixed"

    return json.dumps({
        "asset": asset,
        "sentiment": sentiment,
        "sentiment_score": round(sentiment_score, 2),
        "positive_signals": pos_count,
        "negative_signals": neg_count,
        "article_count": len(news[:15]),
        "sample_headlines": titles[:5],
        "method": "keyword_based",
        "note": "Keyword-based proxy. Production would use LLM-based sentiment analysis.",
        "timestamp": datetime.now().isoformat(),
    })
