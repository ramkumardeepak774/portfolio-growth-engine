"""Base collector with shared HTTP client and rate-limiting."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Base class for all data collectors.

    Provides:
    - Async HTTP client with timeout & retries
    - Rate-limit–aware request method
    - Consistent logging
    """

    def __init__(self, name: str, rate_limit_per_min: int = 60):
        self.name = name
        self._rate_limit = rate_limit_per_min
        self._request_times: list[float] = []
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _rate_limited_request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request with rate limiting and retries."""
        # Simple sliding-window rate limiter
        now = asyncio.get_event_loop().time()
        self._request_times = [t for t in self._request_times if now - t < 60]
        if len(self._request_times) >= self._rate_limit:
            wait = 60 - (now - self._request_times[0])
            logger.info(f"[{self.name}] Rate limit hit, waiting {wait:.1f}s")
            await asyncio.sleep(wait)

        client = await self._get_client()
        for attempt in range(3):
            try:
                self._request_times.append(asyncio.get_event_loop().time())
                resp = await client.request(method, url, **kwargs)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait = 2 ** attempt * 5
                    logger.warning(f"[{self.name}] 429 rate-limited, retry in {wait}s")
                    await asyncio.sleep(wait)
                    continue
                raise
            except httpx.RequestError as e:
                if attempt < 2:
                    logger.warning(f"[{self.name}] Request error: {e}, retrying...")
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

        raise RuntimeError(f"[{self.name}] Failed after 3 retries: {url}")

    async def get_json(self, url: str, params: dict | None = None) -> Any:
        resp = await self._rate_limited_request("GET", url, params=params)
        return resp.json()

    @abstractmethod
    async def collect(self, symbol: str, **kwargs) -> dict:
        """Collect data for a given symbol. Returns structured data."""
        ...
