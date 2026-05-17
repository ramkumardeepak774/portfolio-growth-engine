"""Finnhub collector — news, sentiment, insider transactions, earnings."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from ..config import get_settings
from ..db.models import DataSource, SentimentLabel
from .base import BaseCollector

logger = logging.getLogger(__name__)

FINNHUB_BASE = "https://finnhub.io/api/v1"


class FinnhubCollector(BaseCollector):
    """Collector for Finnhub API.

    Free tier: 60 calls/min. Covers:
    - Company news
    - Market news
    - Earnings calendar
    - Insider transactions
    - Basic sentiment
    """

    def __init__(self):
        super().__init__("finnhub", rate_limit_per_min=55)
        self._token = get_settings().finnhub_key

    def _params(self, extra: dict | None = None) -> dict:
        p = {"token": self._token}
        if extra:
            p.update(extra)
        return p

    async def collect(self, symbol: str, **kwargs) -> dict:
        return {
            "news": await self.collect_news(symbol),
            "sentiment": await self.collect_sentiment(symbol),
        }

    async def collect_news(self, symbol: str, days_back: int = 30) -> list[dict]:
        """Collect company news articles."""
        try:
            from_date = (date.today() - timedelta(days=days_back)).isoformat()
            to_date = date.today().isoformat()

            data = await self.get_json(
                f"{FINNHUB_BASE}/company-news",
                params=self._params({
                    "symbol": symbol,
                    "from": from_date,
                    "to": to_date,
                }),
            )

            return [
                {
                    "title": item.get("headline", ""),
                    "url": item.get("url", ""),
                    "published_at": datetime.fromtimestamp(item["datetime"]) if item.get("datetime") else None,
                    "source_name": item.get("source", ""),
                    "content_snippet": item.get("summary", ""),
                    "source": DataSource.FINNHUB,
                }
                for item in (data or [])[:50]
            ]
        except Exception as e:
            logger.warning(f"Finnhub news failed for {symbol}: {e}")
            return []

    async def collect_sentiment(self, symbol: str) -> dict | None:
        """Collect social sentiment metrics."""
        try:
            data = await self.get_json(
                f"{FINNHUB_BASE}/stock/social-sentiment",
                params=self._params({"symbol": symbol}),
            )
            if not data:
                return None

            reddit = data.get("reddit", [])
            twitter = data.get("twitter", [])

            return {
                "reddit_mentions": sum(p.get("mention", 0) for p in reddit),
                "reddit_positive": sum(p.get("positiveScore", 0) for p in reddit),
                "reddit_negative": sum(p.get("negativeScore", 0) for p in reddit),
                "twitter_mentions": sum(p.get("mention", 0) for p in twitter),
                "twitter_positive": sum(p.get("positiveScore", 0) for p in twitter),
                "twitter_negative": sum(p.get("negativeScore", 0) for p in twitter),
            }
        except Exception as e:
            logger.warning(f"Finnhub sentiment failed for {symbol}: {e}")
            return None

    async def collect_market_news(self, category: str = "general") -> list[dict]:
        """Collect general market news."""
        try:
            data = await self.get_json(
                f"{FINNHUB_BASE}/news",
                params=self._params({"category": category}),
            )
            return [
                {
                    "title": item.get("headline", ""),
                    "url": item.get("url", ""),
                    "published_at": datetime.fromtimestamp(item["datetime"]) if item.get("datetime") else None,
                    "source_name": item.get("source", ""),
                    "content_snippet": item.get("summary", ""),
                    "source": DataSource.FINNHUB,
                }
                for item in (data or [])[:30]
            ]
        except Exception as e:
            logger.warning(f"Finnhub market news failed: {e}")
            return []

    async def collect_earnings_calendar(self, from_date: str | None = None, to_date: str | None = None) -> list[dict]:
        """Upcoming earnings dates."""
        try:
            from_d = from_date or date.today().isoformat()
            to_d = to_date or (date.today() + timedelta(days=30)).isoformat()

            data = await self.get_json(
                f"{FINNHUB_BASE}/calendar/earnings",
                params=self._params({"from": from_d, "to": to_d}),
            )
            return data.get("earningsCalendar", []) if data else []
        except Exception as e:
            logger.warning(f"Finnhub earnings calendar failed: {e}")
            return []
