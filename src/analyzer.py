"""Portfolio performance analysis engine."""

from __future__ import annotations

import math
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd
from pyxirr import xirr

from .models import (
    AssetClass,
    Holding,
    Portfolio,
    TransactionType,
)


# Annualizing a return over less than a week of holding history isn't
# meaningful — extrapolating one day of price movement to a full year
# produces numbers that are either absurd (a 2x return in a day "is"
# 2^365 % annualized) or literally overflow a float for larger returns.
# CSV-imported holdings (bought "today", no real trade history) hit this
# constantly, so it's a real guard, not a hypothetical one.
_MIN_YEARS_FOR_ANNUALIZATION = 7 / 365.25


def calculate_cagr(initial: float, final: float, years: float) -> float:
    """Calculate Compound Annual Growth Rate."""
    if initial <= 0 or years < _MIN_YEARS_FOR_ANNUALIZATION:
        return 0.0
    try:
        return ((final / initial) ** (1 / years) - 1) * 100
    except OverflowError:
        # Defensive backstop — even beyond the minimum-years guard above,
        # an extreme enough ratio can still overflow a float.
        return 0.0


def calculate_xirr(holding: Holding) -> Optional[float]:
    """Calculate XIRR for a holding (accounts for irregular cashflows like SIPs).

    Returns annualized return as a percentage, or None if calculation fails.
    """
    dates = []
    amounts = []

    for t in holding.transactions:
        if t.type in (TransactionType.BUY, TransactionType.SIP):
            dates.append(t.date)
            amounts.append(-t.amount)  # outflow
        elif t.type == TransactionType.SELL:
            dates.append(t.date)
            amounts.append(t.amount)  # inflow
        elif t.type == TransactionType.DIVIDEND:
            dates.append(t.date)
            amounts.append(t.quantity * t.price)  # inflow

    # Add current value as final inflow
    if holding.current_value > 0:
        dates.append(date.today())
        amounts.append(holding.current_value)

    if len(dates) < 2:
        return None
    if (max(dates) - min(dates)).days / 365.25 < _MIN_YEARS_FOR_ANNUALIZATION:
        # Not just an inf/nan risk — even when pyxirr returns a finite
        # number here, annualizing a few days of price movement produces
        # nonsense-magnitude percentages, not a meaningful XIRR.
        return None

    try:
        result = xirr(dates, amounts)
        if result is not None and math.isfinite(result):
            return result * 100
    except Exception:
        pass
    return None


def calculate_portfolio_cagr(portfolio: Portfolio) -> float:
    """Simple CAGR based on total invested vs current value."""
    # Find the earliest transaction date across all holdings
    earliest = None
    for h in portfolio.holdings:
        fd = h.first_investment_date
        if fd and (earliest is None or fd < earliest):
            earliest = fd

    if earliest is None:
        return 0.0

    years = (date.today() - earliest).days / 365.25
    return calculate_cagr(portfolio.total_invested, portfolio.total_current_value, years)


def calculate_portfolio_xirr(portfolio: Portfolio) -> Optional[float]:
    """Calculate XIRR across the entire portfolio."""
    dates = []
    amounts = []

    for h in portfolio.holdings:
        for t in h.transactions:
            if t.type in (TransactionType.BUY, TransactionType.SIP):
                dates.append(t.date)
                amounts.append(-t.amount)
            elif t.type == TransactionType.SELL:
                dates.append(t.date)
                amounts.append(t.amount)
            elif t.type == TransactionType.DIVIDEND:
                dates.append(t.date)
                amounts.append(t.quantity * t.price)

    # Current portfolio value as final inflow
    if portfolio.total_current_value > 0:
        dates.append(date.today())
        amounts.append(portfolio.total_current_value)

    if len(dates) < 2:
        return None
    if (max(dates) - min(dates)).days / 365.25 < _MIN_YEARS_FOR_ANNUALIZATION:
        return None

    try:
        result = xirr(dates, amounts)
        if result is not None and math.isfinite(result):
            return result * 100
    except Exception:
        pass
    return None


def asset_class_allocation(portfolio: Portfolio) -> dict[str, dict]:
    """Break down portfolio by asset class.

    Returns dict like:
      {"equity_large_cap": {"value": 500000, "percent": 25.0, "count": 3}, ...}
    """
    total = portfolio.total_current_value
    allocation = {}

    for ac, holdings in portfolio.holdings_by_asset_class().items():
        value = sum(h.current_value for h in holdings)
        pct = (value / total * 100) if total > 0 else 0
        allocation[ac.value] = {
            "label": ac.name.replace("_", " ").title(),
            "value": value,
            "percent": round(pct, 2),
            "count": len(holdings),
        }

    return dict(sorted(allocation.items(), key=lambda x: -x[1]["value"]))


def sector_allocation(portfolio: Portfolio) -> dict[str, dict]:
    """Break down portfolio by sector."""
    total = portfolio.total_current_value
    allocation = {}

    for sector, holdings in portfolio.holdings_by_sector().items():
        value = sum(h.current_value for h in holdings)
        pct = (value / total * 100) if total > 0 else 0
        allocation[sector] = {
            "value": value,
            "percent": round(pct, 2),
            "count": len(holdings),
        }

    return dict(sorted(allocation.items(), key=lambda x: -x[1]["value"]))


def concentration_risk(portfolio: Portfolio, top_n: int = 5) -> dict:
    """Analyze concentration risk — how much is in top N holdings."""
    total = portfolio.total_current_value
    if total <= 0:
        return {"top_holdings": [], "top_percent": 0}

    sorted_holdings = sorted(portfolio.holdings, key=lambda h: -h.current_value)
    top = sorted_holdings[:top_n]
    top_value = sum(h.current_value for h in top)

    return {
        "top_holdings": [
            {
                "symbol": h.symbol,
                "name": h.name,
                "value": h.current_value,
                "percent": round(h.current_value / total * 100, 2),
            }
            for h in top
        ],
        "top_value": top_value,
        "top_percent": round(top_value / total * 100, 2),
    }


# Asset classes with a reliable daily price series on Yahoo Finance.
# Mutual funds, gold, FD/PPF/EPF/NPS, real estate, and cash have no such
# series, so they're excluded from the reconstructed value series below —
# it reflects direct equity holdings only, not the full multi-asset portfolio.
_PRICEABLE_ASSET_CLASSES = {
    AssetClass.EQUITY_LARGE_CAP,
    AssetClass.EQUITY_MID_CAP,
    AssetClass.EQUITY_SMALL_CAP,
    AssetClass.EQUITY_MICRO_CAP,
}


def _quantity_as_of(holding: Holding, as_of: date) -> float:
    """Units held at close of `as_of`, reconstructed from transaction history."""
    qty = 0.0
    for t in holding.transactions:
        if t.date > as_of:
            continue
        if t.type in (TransactionType.BUY, TransactionType.SIP):
            qty += t.quantity
        elif t.type == TransactionType.SELL:
            qty -= t.quantity
    return qty


def portfolio_value_series(portfolio: Portfolio, period: str = "1y") -> list[dict]:
    """Reconstruct real weighted portfolio value across a date range.

    For each date, sums (quantity held at that date × close price on that
    date) across priceable holdings. Quantity comes from transaction
    history; price comes from the Postgres-cached Yahoo Finance series.
    """
    from .price_cache import get_price_history

    price_series: dict[str, pd.Series] = {}
    all_dates: set[date] = set()

    for h in portfolio.holdings:
        if h.asset_class not in _PRICEABLE_ASSET_CLASSES:
            continue
        df = get_price_history(h.symbol, h.asset_class, period=period)
        if df is None or df.empty:
            continue
        df = df.copy()
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        series = df.set_index("Date")["Close"].sort_index()
        price_series[h.symbol] = series
        all_dates.update(series.index)

    if not all_dates:
        return []

    rows = []
    for d in sorted(all_dates):
        total = 0.0
        contributing = 0
        for h in portfolio.holdings:
            series = price_series.get(h.symbol)
            if series is None:
                continue
            available = series[series.index <= d]
            if available.empty:
                continue
            price = available.iloc[-1]
            qty = _quantity_as_of(h, d)
            if qty <= 0:
                continue
            total += qty * price
            contributing += 1
        if contributing > 0:
            rows.append({"date": d.isoformat(), "value": round(total, 2)})
    return rows


def holding_performance_table(portfolio: Portfolio) -> pd.DataFrame:
    """Generate a DataFrame with per-holding performance metrics."""
    rows = []
    for h in portfolio.holdings:
        xirr_val = calculate_xirr(h)
        years = 0.0
        if h.first_investment_date:
            years = (date.today() - h.first_investment_date).days / 365.25
        cagr = calculate_cagr(h.invested_amount, h.current_value, years) if years > 0 else 0

        rows.append({
            "Symbol": h.symbol,
            "Name": h.name,
            "Asset Class": h.asset_class.value,
            "Sector": h.sector or "—",
            "Qty": round(h.quantity, 2),
            "Invested (₹)": round(h.invested_amount, 2),
            "Current (₹)": round(h.current_value, 2),
            "P&L (₹)": round(h.pnl, 2),
            "P&L %": round(h.pnl_percent, 2),
            "CAGR %": round(cagr, 2),
            "XIRR %": round(xirr_val, 2) if xirr_val else "N/A",
            "Years Held": round(years, 1),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Current (₹)", ascending=False).reset_index(drop=True)
    return df
