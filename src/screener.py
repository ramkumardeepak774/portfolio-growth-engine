"""Stock and mutual fund screener for research."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class StockScreen:
    symbol: str
    name: str
    sector: str
    market_cap: float  # in Cr
    pe_ratio: float
    pb_ratio: float
    roe: float  # %
    debt_to_equity: float
    dividend_yield: float  # %
    revenue_growth: float  # %
    profit_growth: float  # %
    price: float
    week_52_high: float
    week_52_low: float
    score: float = 0.0  # composite score


def screen_stock(symbol: str) -> Optional[StockScreen]:
    """Fetch and score a single stock."""
    try:
        yahoo_sym = symbol if "." in symbol else f"{symbol}.NS"
        ticker = yf.Ticker(yahoo_sym)
        info = ticker.info

        market_cap_cr = info.get("marketCap", 0) / 1e7  # convert to Cr
        pe = info.get("trailingPE", 0) or 0
        pb = info.get("priceToBook", 0) or 0
        roe = info.get("returnOnEquity", 0) or 0
        roe_pct = roe * 100 if roe < 1 else roe
        de = info.get("debtToEquity", 0) or 0
        div_yield = (info.get("dividendYield", 0) or 0) * 100
        rev_growth = (info.get("revenueGrowth", 0) or 0) * 100
        earnings_growth = (info.get("earningsGrowth", 0) or 0) * 100
        price = info.get("currentPrice", 0) or info.get("regularMarketPrice", 0) or 0
        high52 = info.get("fiftyTwoWeekHigh", 0) or 0
        low52 = info.get("fiftyTwoWeekLow", 0) or 0

        screen = StockScreen(
            symbol=symbol,
            name=info.get("shortName", symbol),
            sector=info.get("sector", "Unknown"),
            market_cap=round(market_cap_cr, 2),
            pe_ratio=round(pe, 2),
            pb_ratio=round(pb, 2),
            roe=round(roe_pct, 2),
            debt_to_equity=round(de, 2),
            dividend_yield=round(div_yield, 2),
            revenue_growth=round(rev_growth, 2),
            profit_growth=round(earnings_growth, 2),
            price=round(price, 2),
            week_52_high=round(high52, 2),
            week_52_low=round(low52, 2),
        )

        # Simple quality score (higher is better)
        screen.score = _calculate_score(screen)
        return screen

    except Exception as e:
        logger.warning(f"Could not screen {symbol}: {e}")
        return None


def _calculate_score(s: StockScreen) -> float:
    """Composite quality score for a stock (0–100 scale).

    Criteria favoring multi-bagger potential:
    - High ROE (>15% is good)
    - Low debt-to-equity (<1 is good)
    - High revenue growth (>15% is great)
    - High profit growth (>20% is great)
    - Reasonable PE (not extreme — <40 preferred)
    - Price near 52-week low = opportunity
    """
    score = 0.0

    # ROE: max 20 pts
    if s.roe >= 25:
        score += 20
    elif s.roe >= 15:
        score += 15
    elif s.roe >= 10:
        score += 8

    # Debt-to-equity: max 15 pts
    if s.debt_to_equity < 0.5:
        score += 15
    elif s.debt_to_equity < 1.0:
        score += 10
    elif s.debt_to_equity < 2.0:
        score += 5

    # Revenue growth: max 20 pts
    if s.revenue_growth >= 30:
        score += 20
    elif s.revenue_growth >= 20:
        score += 15
    elif s.revenue_growth >= 10:
        score += 8

    # Profit growth: max 20 pts
    if s.profit_growth >= 30:
        score += 20
    elif s.profit_growth >= 20:
        score += 15
    elif s.profit_growth >= 10:
        score += 8

    # PE ratio: max 15 pts (value + growth balance)
    if 0 < s.pe_ratio <= 20:
        score += 15
    elif 20 < s.pe_ratio <= 40:
        score += 10
    elif 40 < s.pe_ratio <= 60:
        score += 5

    # Proximity to 52-week low: max 10 pts
    if s.week_52_high > 0 and s.price > 0:
        range_pos = (s.price - s.week_52_low) / (s.week_52_high - s.week_52_low) if s.week_52_high != s.week_52_low else 0.5
        score += max(0, (1 - range_pos) * 10)

    return round(score, 1)


def screen_multiple(symbols: list[str]) -> list[StockScreen]:
    """Screen multiple stocks and return sorted by score."""
    results = []
    for sym in symbols:
        s = screen_stock(sym)
        if s:
            results.append(s)
    return sorted(results, key=lambda x: -x.score)


# --- Pre-built watchlists for Indian market ---

NIFTY_50_POPULAR = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "TITAN",
    "BAJFINANCE", "WIPRO", "HCLTECH", "ULTRACEMCO", "NESTLEIND",
]

SMALL_CAP_WATCHLIST = [
    "DEEPAKNTR", "AFFLE", "ROUTE", "HAPPSTMNDS", "LATENTVIEW",
    "KAYNES", "SYRMA", "SAGCEM", "MAZDOCK", "COCHINSHIP",
]

MULTI_BAGGER_THEMES = {
    "Defence": ["HAL", "BEL", "MAZDOCK", "COCHINSHIP", "BDL"],
    "EV & Green Energy": ["TATAPOWER", "ADANIGREEN", "SUZLON", "IREDA", "NHPC"],
    "Digital India": ["INFY", "TCS", "LTIM", "COFORGE", "PERSISTENT"],
    "Manufacturing (PLI)": ["DIXON", "KAYNES", "SYRMA", "AMBER", "AVANTEL"],
    "Infra": ["LT", "NCC", "IRCON", "RVNL", "NBCC"],
}
