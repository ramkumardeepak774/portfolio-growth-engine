"""Financial Modeling Prep (FMP) collector — earnings, fundamentals, insider trades."""

from __future__ import annotations

import logging
from datetime import date

from ..config import get_settings
from ..db.models import DataSource
from .base import BaseCollector

logger = logging.getLogger(__name__)

FMP_BASE = "https://financialmodelingprep.com/api/v3"


class FMPCollector(BaseCollector):
    """Collector for Financial Modeling Prep API.

    Free tier: 250 requests/day. Covers:
    - Income statement, balance sheet, cash flow
    - Key metrics, ratios, growth
    - Earnings calendar & surprises
    - Insider trading
    - Stock screener
    """

    def __init__(self):
        super().__init__("fmp", rate_limit_per_min=30)
        self._api_key = get_settings().fmp_key

    def _params(self, extra: dict | None = None) -> dict:
        p = {"apikey": self._api_key}
        if extra:
            p.update(extra)
        return p

    async def collect(self, symbol: str, **kwargs) -> dict:
        """Collect all available FMP data for a symbol."""
        results = {}
        suffix = ".NS" if "." not in symbol else ""
        fmp_symbol = f"{symbol}{suffix}"

        results["income_statement"] = await self._income_statement(fmp_symbol)
        results["key_metrics"] = await self._key_metrics(fmp_symbol)
        results["growth"] = await self._growth(fmp_symbol)
        results["ratios"] = await self._ratios(fmp_symbol)

        return results

    async def collect_earnings(self, symbol: str) -> list[dict]:
        """Get earnings surprises."""
        try:
            data = await self.get_json(
                f"{FMP_BASE}/earnings-surprises/{symbol}",
                params=self._params(),
            )
            return [
                {
                    "report_date": item.get("date"),
                    "eps_actual": item.get("actualEarningResult"),
                    "eps_estimate": item.get("estimatedEarning"),
                    "revenue": item.get("actualRevenue"),
                    "revenue_estimate": item.get("estimatedRevenue"),
                    "source": DataSource.FMP,
                }
                for item in (data or [])[:8]
            ]
        except Exception as e:
            logger.warning(f"FMP earnings failed for {symbol}: {e}")
            return []

    async def collect_insider_trades(self, symbol: str) -> list[dict]:
        """Get insider trading activity."""
        try:
            data = await self.get_json(
                f"{FMP_BASE}/insider-trading",
                params=self._params({"symbol": symbol}),
            )
            return [
                {
                    "insider_name": item.get("reportingName", "Unknown"),
                    "designation": item.get("typeOfOwner"),
                    "trade_type": "buy" if item.get("acquistionOrDisposition") == "A" else "sell",
                    "trade_date": item.get("transactionDate"),
                    "quantity": abs(item.get("securitiesTransacted", 0)),
                    "price": item.get("price", 0),
                    "value": abs(item.get("securitiesTransacted", 0)) * (item.get("price", 0) or 0),
                    "source": DataSource.FMP,
                }
                for item in (data or [])[:20]
            ]
        except Exception as e:
            logger.warning(f"FMP insider trades failed for {symbol}: {e}")
            return []

    async def screen_stocks(self, filters: dict) -> list[dict]:
        """Use FMP stock screener.

        filters: marketCapMoreThan, betaMoreThan, dividendMoreThan,
                 sector, industry, exchange, etc.
        """
        try:
            params = self._params(filters)
            data = await self.get_json(f"{FMP_BASE}/stock-screener", params=params)
            return data or []
        except Exception as e:
            logger.warning(f"FMP screener failed: {e}")
            return []

    async def _income_statement(self, symbol: str) -> list[dict]:
        try:
            data = await self.get_json(
                f"{FMP_BASE}/income-statement/{symbol}",
                params=self._params({"period": "quarter", "limit": 8}),
            )
            return data or []
        except Exception:
            return []

    async def _key_metrics(self, symbol: str) -> list[dict]:
        try:
            data = await self.get_json(
                f"{FMP_BASE}/key-metrics/{symbol}",
                params=self._params({"period": "quarter", "limit": 8}),
            )
            return data or []
        except Exception:
            return []

    async def _growth(self, symbol: str) -> list[dict]:
        try:
            data = await self.get_json(
                f"{FMP_BASE}/financial-growth/{symbol}",
                params=self._params({"period": "quarter", "limit": 8}),
            )
            return data or []
        except Exception:
            return []

    async def _ratios(self, symbol: str) -> list[dict]:
        try:
            data = await self.get_json(
                f"{FMP_BASE}/ratios/{symbol}",
                params=self._params({"period": "quarter", "limit": 8}),
            )
            return data or []
        except Exception:
            return []
