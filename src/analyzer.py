"""Portfolio performance analysis engine."""

from __future__ import annotations

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


def calculate_cagr(initial: float, final: float, years: float) -> float:
    """Calculate Compound Annual Growth Rate."""
    if initial <= 0 or years <= 0:
        return 0.0
    return ((final / initial) ** (1 / years) - 1) * 100


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

    try:
        result = xirr(dates, amounts)
        if result is not None:
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

    try:
        result = xirr(dates, amounts)
        if result is not None:
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
