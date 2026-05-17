"""Reddit sentiment collector — tracks Indian investing subreddits."""

from __future__ import annotations

import logging
from datetime import date, datetime

from ..config import get_settings
from ..db.models import DataSource
from .base import BaseCollector

logger = logging.getLogger(__name__)

# Indian investing subreddits
SUBREDDITS = [
    "IndianStreetBets",
    "IndiaInvestments",
    "IndianStockMarket",
    "DalalStreetTalks",
]

REDDIT_BASE = "https://www.reddit.com"


class RedditCollector(BaseCollector):
    """Collect sentiment from Reddit (public JSON API — no auth needed for reading)."""

    def __init__(self):
        super().__init__("reddit", rate_limit_per_min=30)
        settings = get_settings()
        self._user_agent = settings.reddit_user_agent

    async def _get_client(self):
        import httpx
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": self._user_agent},
            )
        return self._client

    async def collect(self, symbol: str, **kwargs) -> dict:
        """Collect Reddit mentions and sentiment for a symbol."""
        all_posts = []
        for sub in SUBREDDITS:
            posts = await self._search_subreddit(sub, symbol)
            all_posts.extend(posts)

        return {
            "symbol": symbol,
            "platform": "reddit",
            "date": date.today().isoformat(),
            "mentions": len(all_posts),
            "posts": all_posts,
            "source": DataSource.REDDIT,
        }

    async def _search_subreddit(self, subreddit: str, query: str) -> list[dict]:
        """Search a subreddit for mentions of a stock."""
        try:
            data = await self.get_json(
                f"{REDDIT_BASE}/r/{subreddit}/search.json",
                params={
                    "q": query,
                    "sort": "new",
                    "t": "month",
                    "limit": 25,
                    "restrict_sr": "true",
                },
            )

            posts = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                posts.append({
                    "title": post.get("title", ""),
                    "selftext": (post.get("selftext", "") or "")[:300],
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "created_utc": datetime.fromtimestamp(post.get("created_utc", 0)).isoformat(),
                    "subreddit": subreddit,
                })

            return posts

        except Exception as e:
            logger.warning(f"Reddit search failed for r/{subreddit} q={query}: {e}")
            return []

    async def collect_subreddit_hot(self, subreddit: str = "IndianStreetBets", limit: int = 25) -> list[dict]:
        """Get hot posts from a subreddit."""
        try:
            data = await self.get_json(
                f"{REDDIT_BASE}/r/{subreddit}/hot.json",
                params={"limit": limit},
            )

            posts = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                posts.append({
                    "title": post.get("title", ""),
                    "selftext": (post.get("selftext", "") or "")[:300],
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "subreddit": subreddit,
                })
            return posts

        except Exception as e:
            logger.warning(f"Reddit hot failed for r/{subreddit}: {e}")
            return []

    async def collect_trending_tickers(self) -> dict[str, int]:
        """Scan Indian investing subreddits for trending stock mentions."""
        import re

        ticker_counts: dict[str, int] = {}
        # Common NSE ticker pattern: all-caps 3-15 chars
        ticker_pattern = re.compile(r'\b([A-Z]{3,15})\b')

        for sub in SUBREDDITS:
            posts = await self.collect_subreddit_hot(sub, limit=50)
            for post in posts:
                text = post["title"] + " " + post.get("selftext", "")
                matches = ticker_pattern.findall(text)
                for match in matches:
                    # Filter common English words
                    if match not in _COMMON_WORDS and len(match) >= 3:
                        ticker_counts[match] = ticker_counts.get(match, 0) + 1

        # Sort by frequency
        return dict(sorted(ticker_counts.items(), key=lambda x: -x[1])[:30])


_COMMON_WORDS = {
    "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN", "HER",
    "WAS", "ONE", "OUR", "OUT", "HAS", "HIS", "HOW", "ITS", "LET", "MAY",
    "NEW", "NOW", "OLD", "SEE", "WAY", "WHO", "DID", "GET", "HIM", "HAD",
    "SAY", "SHE", "TOO", "USE", "BUY", "SELL", "IPO", "SIP", "ETF", "NFO",
    "FII", "DII", "AGM", "EPS", "ROE", "ROA", "MIS", "CNC", "GTT", "AMO",
    "PUT", "CALL", "YOLO", "HODL", "IMO", "TLDR", "PSU", "BSE", "NSE",
    "NIFTY", "BANK", "SENSEX", "EDIT", "UPDATE", "HELP", "NEED", "WANT",
    "JUST", "LIKE", "WHAT", "THIS", "THAT", "WITH", "HAVE", "FROM", "WILL",
    "BEEN", "MORE", "WHEN", "THAN", "SOME", "VERY", "THEM", "INTO", "ALSO",
    "OVER", "SUCH", "ONLY", "THEN", "BEST", "LONG", "SHORT", "HIGH", "LOW",
}
