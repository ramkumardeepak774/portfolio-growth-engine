"""Layer 1 API — Data collection and retrieval."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Query

from ..collectors.yahoo_collector import YahooCollector
from ..collectors.news_collector import NewsCollector
from ..collectors.reddit_collector import RedditCollector
from ..config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/fundamentals/{symbol}")
async def get_fundamentals(symbol: str):
    """Fetch fundamentals for a stock (Yahoo Finance)."""
    collector = YahooCollector()
    # yfinance is fully synchronous — run it off the event loop so a slow
    # or failing Yahoo request doesn't stall every other concurrent request
    # on this single-process server (this blocked the whole dashboard once).
    data = await asyncio.to_thread(collector.collect_fundamentals, symbol.upper())
    if not data:
        raise HTTPException(404, f"No data found for {symbol}")
    return data


@router.get("/prices/{symbol}")
async def get_prices(symbol: str, period: str = Query("1y", pattern="^(1mo|3mo|6mo|1y|2y|5y|max)$")):
    """Fetch historical prices."""
    collector = YahooCollector()
    df = await asyncio.to_thread(collector.collect_prices, symbol.upper(), period=period)
    if df is None or df.empty:
        raise HTTPException(404, f"No price data for {symbol}")
    return df.to_dict(orient="records")


@router.get("/earnings/{symbol}")
async def get_earnings(symbol: str):
    """Fetch earnings data."""
    collector = YahooCollector()
    data = await asyncio.to_thread(collector.collect_earnings, symbol.upper())
    return {"symbol": symbol.upper(), "earnings": data}


@router.get("/insider/{symbol}")
async def get_insider_trades(symbol: str):
    """Fetch insider trading data."""
    collector = YahooCollector()
    data = await asyncio.to_thread(collector.collect_insider_trades, symbol.upper())
    return {"symbol": symbol.upper(), "insider_trades": data}


@router.get("/news")
async def get_news(symbol: str | None = None):
    """Fetch financial news, optionally filtered by symbol."""
    collector = NewsCollector()
    try:
        if symbol:
            result = await collector.collect(symbol.upper())
            return result
        else:
            articles = await collector.collect_india_market_news()
            return {"articles": articles[:30]}
    finally:
        await collector.close()


@router.get("/reddit/sentiment/{symbol}")
async def get_reddit_sentiment(symbol: str):
    """Fetch Reddit sentiment for a stock."""
    collector = RedditCollector()
    try:
        data = await collector.collect(symbol.upper())
        return data
    finally:
        await collector.close()


@router.get("/reddit/trending")
async def get_reddit_trending():
    """Get trending stock tickers from Indian investing subreddits."""
    collector = RedditCollector()
    try:
        trending = await collector.collect_trending_tickers()
        return {"trending_tickers": trending}
    finally:
        await collector.close()


@router.get("/finnhub/news/{symbol}")
async def get_finnhub_news(symbol: str):
    """Fetch news from Finnhub (requires API key)."""
    settings = get_settings()
    if not settings.has_finnhub:
        raise HTTPException(400, "Finnhub API key not configured")

    from ..collectors.finnhub_collector import FinnhubCollector
    collector = FinnhubCollector()
    try:
        data = await collector.collect_news(symbol.upper())
        return {"symbol": symbol.upper(), "news": data}
    finally:
        await collector.close()


@router.post("/collect/{symbol}")
async def trigger_full_collection(symbol: str):
    """Trigger full data collection for a symbol (background task)."""
    from ..tasks import collect_all_for_symbol
    task = collect_all_for_symbol.delay(symbol.upper())
    return {"task_id": task.id, "symbol": symbol.upper(), "status": "queued"}
