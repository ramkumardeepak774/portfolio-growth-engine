"""Yahoo Finance collector — fundamentals, prices, earnings. No API key needed."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import pandas as pd
import yfinance as yf

from ..db.models import DataSource

logger = logging.getLogger(__name__)

NSE_SUFFIX = ".NS"


def _yahoo_symbol(symbol: str) -> str:
    # Index tickers (e.g. ^NSEI for NIFTY 50) already are the Yahoo symbol —
    # appending .NS turns them into a nonexistent ticker (^NSEI.NS 404s).
    if symbol.startswith("^") or "." in symbol:
        return symbol
    return f"{symbol}{NSE_SUFFIX}"


class YahooCollector:
    """Synchronous Yahoo Finance collector (yfinance is sync)."""

    name = "yahoo"

    def collect_fundamentals(self, symbol: str) -> dict | None:
        """Collect fundamental data for a stock."""
        try:
            ticker = yf.Ticker(_yahoo_symbol(symbol))
            info = ticker.info
            if not info or "symbol" not in info:
                return None

            return {
                "symbol": symbol,
                "source": DataSource.YAHOO,
                "period_type": "ttm",
                "period_end": date.today(),
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "ps_ratio": info.get("priceToSalesTrailing12Months"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "market_cap": info.get("marketCap"),
                "revenue": info.get("totalRevenue"),
                "net_income": info.get("netIncomeToCommon"),
                "ebitda": info.get("ebitda"),
                "gross_margin": _pct(info.get("grossMargins")),
                "operating_margin": _pct(info.get("operatingMargins")),
                "net_margin": _pct(info.get("profitMargins")),
                "roe": _pct(info.get("returnOnEquity")),
                "roa": _pct(info.get("returnOnAssets")),
                "revenue_growth_yoy": _pct(info.get("revenueGrowth")),
                "profit_growth_yoy": _pct(info.get("earningsGrowth")),
                "eps": info.get("trailingEps"),
                "total_debt": info.get("totalDebt"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "free_cash_flow": info.get("freeCashflow"),
                "cash_and_equivalents": info.get("totalCash"),
                "dividend_yield": _pct(info.get("dividendYield")),
                "payout_ratio": _pct(info.get("payoutRatio")),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "name": info.get("shortName", symbol),
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            }
        except Exception as e:
            logger.warning(f"Yahoo fundamentals failed for {symbol}: {e}")
            return None

    def collect_prices(self, symbol: str, period: str = "2y") -> pd.DataFrame | None:
        """Collect historical OHLCV prices."""
        try:
            ticker = yf.Ticker(_yahoo_symbol(symbol))
            hist = ticker.history(period=period)
            if hist.empty:
                return None
            hist = hist.reset_index()
            hist.columns = [c.lower().replace(" ", "_") for c in hist.columns]
            return hist
        except Exception as e:
            logger.warning(f"Yahoo prices failed for {symbol}: {e}")
            return None

    def collect_earnings(self, symbol: str) -> list[dict]:
        """Collect earnings data."""
        try:
            ticker = yf.Ticker(_yahoo_symbol(symbol))
            earnings = ticker.earnings_dates
            if earnings is None or earnings.empty:
                return []

            results = []
            for idx, row in earnings.iterrows():
                results.append({
                    "report_date": idx.date() if hasattr(idx, "date") else date.today(),
                    "eps_actual": row.get("Reported EPS"),
                    "eps_estimate": row.get("EPS Estimate"),
                    "surprise_pct": row.get("Surprise(%)"),
                })
            return results
        except Exception as e:
            logger.warning(f"Yahoo earnings failed for {symbol}: {e}")
            return []

    def collect_insider_trades(self, symbol: str) -> list[dict]:
        """Collect insider transaction data."""
        try:
            ticker = yf.Ticker(_yahoo_symbol(symbol))
            insiders = ticker.insider_transactions
            if insiders is None or insiders.empty:
                return []

            results = []
            for _, row in insiders.iterrows():
                results.append({
                    "insider_name": row.get("Insider", "Unknown"),
                    "trade_type": "buy" if "buy" in str(row.get("Transaction", "")).lower() else "sell",
                    "trade_date": row.get("Start Date", date.today()),
                    "quantity": abs(row.get("Shares", 0)),
                    "value": abs(row.get("Value", 0)),
                })
            return results
        except Exception as e:
            logger.warning(f"Yahoo insider trades failed for {symbol}: {e}")
            return []


def _pct(val) -> float | None:
    """Convert ratio (0.15) to percent (15.0)."""
    if val is None:
        return None
    v = float(val)
    return v * 100 if abs(v) < 5 else v  # already in % if > 5
