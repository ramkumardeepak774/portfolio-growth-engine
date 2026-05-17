"""Celery tasks — background data collection and processing."""

from __future__ import annotations

import logging
from datetime import date

from .worker import celery_app

logger = logging.getLogger(__name__)


def _get_watchlist_symbols() -> list[str]:
    """Get all symbols we're tracking from the database or config."""
    # For now, return from portfolio YAML; later this reads from DB
    try:
        from .portfolio import load_portfolio
        portfolio = load_portfolio()
        return [h.symbol for h in portfolio.holdings]
    except Exception:
        return []


@celery_app.task(name="src.tasks.collect_prices_all")
def collect_prices_all():
    """Collect daily prices for all tracked symbols."""
    from .collectors.yahoo_collector import YahooCollector

    collector = YahooCollector()
    symbols = _get_watchlist_symbols()
    results = {"success": 0, "failed": 0}

    for symbol in symbols:
        try:
            prices = collector.collect_prices(symbol, period="5d")
            if prices is not None and not prices.empty:
                results["success"] += 1
                logger.info(f"Collected {len(prices)} price records for {symbol}")
                # TODO: Insert into DB when PostgreSQL is configured
            else:
                results["failed"] += 1
        except Exception as e:
            results["failed"] += 1
            logger.warning(f"Price collection failed for {symbol}: {e}")

    logger.info(f"Price collection complete: {results}")
    return results


@celery_app.task(name="src.tasks.collect_fundamentals_all")
def collect_fundamentals_all():
    """Collect fundamentals for all tracked symbols."""
    from .collectors.yahoo_collector import YahooCollector

    collector = YahooCollector()
    symbols = _get_watchlist_symbols()
    results = {"success": 0, "failed": 0}

    for symbol in symbols:
        try:
            data = collector.collect_fundamentals(symbol)
            if data:
                results["success"] += 1
                logger.info(f"Collected fundamentals for {symbol}")
                # TODO: Upsert into DB
            else:
                results["failed"] += 1
        except Exception as e:
            results["failed"] += 1
            logger.warning(f"Fundamentals collection failed for {symbol}: {e}")

    logger.info(f"Fundamentals collection complete: {results}")
    return results


@celery_app.task(name="src.tasks.collect_news_all")
def collect_news_all():
    """Collect news from RSS feeds."""
    import asyncio
    from .collectors.news_collector import NewsCollector

    async def _run():
        collector = NewsCollector()
        try:
            articles = await collector.collect_all_feeds()
            logger.info(f"Collected {len(articles)} news articles")
            return len(articles)
        finally:
            await collector.close()

    count = asyncio.run(_run())
    return {"articles_collected": count}


@celery_app.task(name="src.tasks.collect_reddit_sentiment")
def collect_reddit_sentiment():
    """Collect Reddit sentiment for tracked symbols."""
    import asyncio
    from .collectors.reddit_collector import RedditCollector

    async def _run():
        collector = RedditCollector()
        try:
            trending = await collector.collect_trending_tickers()
            logger.info(f"Reddit trending tickers: {list(trending.keys())[:10]}")

            symbols = _get_watchlist_symbols()
            for symbol in symbols[:10]:  # Limit to avoid rate limits
                data = await collector.collect(symbol)
                logger.info(f"Reddit: {symbol} — {data['mentions']} mentions")

            return {"trending_count": len(trending), "symbols_scanned": len(symbols)}
        finally:
            await collector.close()

    return asyncio.run(_run())


@celery_app.task(name="src.tasks.take_portfolio_snapshot")
def take_portfolio_snapshot():
    """Take a daily portfolio snapshot."""
    from .portfolio import load_portfolio
    from .analyzer import (
        calculate_portfolio_cagr,
        calculate_portfolio_xirr,
        asset_class_allocation,
        sector_allocation,
        concentration_risk,
    )

    portfolio = load_portfolio()

    snapshot = {
        "date": date.today().isoformat(),
        "total_invested": portfolio.total_invested,
        "total_value": portfolio.total_current_value,
        "total_pnl": portfolio.total_pnl,
        "total_pnl_pct": portfolio.total_pnl_percent,
        "cagr": calculate_portfolio_cagr(portfolio),
        "xirr": calculate_portfolio_xirr(portfolio),
        "allocation_by_class": asset_class_allocation(portfolio),
        "allocation_by_sector": sector_allocation(portfolio),
        "concentration_top5": concentration_risk(portfolio),
    }

    logger.info(f"Portfolio snapshot: value={snapshot['total_value']}, pnl={snapshot['total_pnl_pct']:.1f}%")
    # TODO: Insert into portfolio_snapshots table
    return snapshot


@celery_app.task(name="src.tasks.collect_all_for_symbol")
def collect_all_for_symbol(symbol: str):
    """Collect everything available for a single symbol."""
    from .collectors.yahoo_collector import YahooCollector
    import asyncio

    results = {}

    # Yahoo (sync)
    yahoo = YahooCollector()
    results["fundamentals"] = yahoo.collect_fundamentals(symbol)
    results["prices"] = yahoo.collect_prices(symbol, period="1y") is not None
    results["earnings"] = yahoo.collect_earnings(symbol)
    results["insider_trades"] = yahoo.collect_insider_trades(symbol)

    # Async collectors
    async def _async_collect():
        from .collectors.finnhub_collector import FinnhubCollector
        from .collectors.reddit_collector import RedditCollector
        from .config import get_settings

        settings = get_settings()

        if settings.has_finnhub:
            finnhub = FinnhubCollector()
            try:
                results["finnhub_news"] = await finnhub.collect_news(symbol)
                results["finnhub_sentiment"] = await finnhub.collect_sentiment(symbol)
            finally:
                await finnhub.close()

        reddit = RedditCollector()
        try:
            results["reddit"] = await reddit.collect(symbol)
        finally:
            await reddit.close()

    asyncio.run(_async_collect())

    logger.info(f"Collected all data for {symbol}: {list(results.keys())}")
    return {k: bool(v) for k, v in results.items()}
