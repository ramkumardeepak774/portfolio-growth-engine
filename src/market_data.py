"""Fetch market data for Indian stocks and mutual funds."""

from __future__ import annotations

import logging
from typing import Optional

import yfinance as yf

from .models import AssetClass, Holding, Portfolio

logger = logging.getLogger(__name__)

# Indian stocks on yfinance use .NS (NSE) or .BO (BSE) suffix
NSE_SUFFIX = ".NS"
BSE_SUFFIX = ".BO"


def _get_yahoo_symbol(symbol: str, asset_class: AssetClass) -> str:
    """Convert local symbol to Yahoo Finance symbol."""
    # If already has a suffix, use as-is
    if "." in symbol:
        return symbol
    # Mutual funds don't have Yahoo symbols — skip
    if asset_class.value.startswith("mf_"):
        return symbol
    # Default to NSE
    return f"{symbol}{NSE_SUFFIX}"


def fetch_current_price(symbol: str, asset_class: AssetClass) -> Optional[float]:
    """Fetch current market price for a single security."""
    try:
        yahoo_sym = _get_yahoo_symbol(symbol, asset_class)
        ticker = yf.Ticker(yahoo_sym)
        info = ticker.info
        # Try multiple price fields
        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
            or info.get("navPrice")
        )
        if price:
            return float(price)
    except Exception as e:
        logger.warning(f"Could not fetch price for {symbol}: {e}")
    return None


def fetch_historical_prices(symbol: str, asset_class: AssetClass, period: str = "5y"):
    """Fetch historical price data as a pandas DataFrame."""
    try:
        yahoo_sym = _get_yahoo_symbol(symbol, asset_class)
        ticker = yf.Ticker(yahoo_sym)
        hist = ticker.history(period=period)
        return hist
    except Exception as e:
        logger.warning(f"Could not fetch history for {symbol}: {e}")
        return None


def update_portfolio_prices(portfolio: Portfolio, skip_mf: bool = False) -> int:
    """Update current prices for all holdings. Returns count of updated holdings."""
    updated = 0
    for holding in portfolio.holdings:
        if skip_mf and holding.asset_class.value.startswith("mf_"):
            continue
        price = fetch_current_price(holding.symbol, holding.asset_class)
        if price is not None:
            holding.current_price = price
            updated += 1
        else:
            logger.info(f"Skipped {holding.symbol} — no price data")
    return updated


def get_stock_info(symbol: str) -> dict:
    """Get detailed stock info from Yahoo Finance."""
    try:
        yahoo_sym = symbol if "." in symbol else f"{symbol}{NSE_SUFFIX}"
        ticker = yf.Ticker(yahoo_sym)
        return ticker.info
    except Exception as e:
        logger.warning(f"Could not fetch info for {symbol}: {e}")
        return {}
