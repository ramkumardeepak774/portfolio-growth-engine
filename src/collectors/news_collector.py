"""News & RSS feed collector — aggregates financial news from multiple sources."""

from __future__ import annotations

import logging
from datetime import datetime
from time import mktime
from typing import Optional

import feedparser

from ..db.models import DataSource
from .base import BaseCollector

logger = logging.getLogger(__name__)


# Curated Indian financial news RSS feeds
INDIA_FINANCE_FEEDS = {
    "moneycontrol": "https://www.moneycontrol.com/rss/latestnews.xml",
    "economic_times_markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "livemint_markets": "https://www.livemint.com/rss/markets",
    "business_standard": "https://www.business-standard.com/rss/markets-106.rss",
}

GLOBAL_FEEDS = {
    "reuters_business": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
    "cnbc": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
}


class NewsCollector(BaseCollector):
    """Collect news from RSS feeds."""

    def __init__(self):
        super().__init__("news_rss", rate_limit_per_min=120)

    async def collect(self, symbol: str, **kwargs) -> dict:
        """Collect news mentioning a symbol from all feeds."""
        all_articles = await self.collect_all_feeds()
        # Filter for symbol mention
        relevant = [
            a for a in all_articles
            if symbol.lower() in (a.get("title", "") + " " + a.get("content_snippet", "")).lower()
        ]
        return {"articles": relevant, "total_scanned": len(all_articles)}

    async def collect_all_feeds(self, feeds: dict[str, str] | None = None) -> list[dict]:
        """Collect articles from all configured RSS feeds."""
        feeds = feeds or {**INDIA_FINANCE_FEEDS, **GLOBAL_FEEDS}
        articles = []

        for source_name, url in feeds.items():
            try:
                feed_articles = self._parse_feed(url, source_name)
                articles.extend(feed_articles)
            except Exception as e:
                logger.warning(f"RSS feed failed for {source_name}: {e}")

        return articles

    def _parse_feed(self, url: str, source_name: str) -> list[dict]:
        """Parse a single RSS feed."""
        feed = feedparser.parse(url)
        articles = []

        for entry in feed.entries[:20]:  # limit per feed
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime.fromtimestamp(mktime(entry.published_parsed))

            articles.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "published_at": published,
                "source_name": source_name,
                "content_snippet": _clean_html(entry.get("summary", "")),
                "source": DataSource.NEWS_RSS,
            })

        return articles

    async def collect_india_market_news(self) -> list[dict]:
        """Collect only from Indian financial news sources."""
        return await self.collect_all_feeds(INDIA_FINANCE_FEEDS)


def _clean_html(text: str) -> str:
    """Strip HTML tags from text."""
    from bs4 import BeautifulSoup
    return BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)[:500]
