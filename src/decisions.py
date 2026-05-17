"""Layer 3 — Portfolio Decision System.

Tracks allocation, risk exposure, concentration, conviction, and enforces
capital allocation discipline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd

from .models import Portfolio, Holding

logger = logging.getLogger(__name__)


@dataclass
class PositionRisk:
    """Risk metrics for a single position."""
    symbol: str
    allocation_pct: float
    max_drawdown_pct: float
    beta: float
    volatility_30d: float
    conviction: str  # from position metadata
    risk_reward: float
    position_score: float  # overall position quality score


@dataclass
class PortfolioRiskReport:
    """Complete portfolio risk dashboard."""
    total_value: float
    total_invested: float

    # Allocation
    top5_concentration_pct: float
    sector_max_pct: float
    largest_position_pct: float
    asset_class_breakdown: dict[str, float]

    # Risk
    portfolio_beta: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    var_95_pct: float  # Value at Risk — 95% confidence

    # Decision quality
    avg_conviction: float
    positions_without_thesis: int
    positions_without_stop_loss: int
    expired_time_horizons: int  # positions past their intended hold period

    # Warnings
    warnings: list[str]
    position_risks: list[PositionRisk]


def calculate_drawdown_series(prices: pd.Series) -> pd.Series:
    """Calculate running drawdown from a price series."""
    peak = prices.expanding().max()
    drawdown = (prices - peak) / peak
    return drawdown


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.065,  # India 10Y ~6.5%
    periods_per_year: int = 252,
) -> float:
    """Annualized Sharpe ratio."""
    if returns.empty or returns.std() == 0:
        return 0.0
    excess_return = returns.mean() * periods_per_year - risk_free_rate
    volatility = returns.std() * np.sqrt(periods_per_year)
    return excess_return / volatility if volatility > 0 else 0.0


def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.065,
    periods_per_year: int = 252,
) -> float:
    """Sortino ratio — uses downside deviation only."""
    if returns.empty:
        return 0.0
    excess_return = returns.mean() * periods_per_year - risk_free_rate
    downside = returns[returns < 0]
    downside_std = downside.std() * np.sqrt(periods_per_year) if len(downside) > 0 else 0.001
    return excess_return / downside_std if downside_std > 0 else 0.0


def calculate_var_95(returns: pd.Series) -> float:
    """Value at Risk at 95% confidence (as a positive percentage)."""
    if returns.empty:
        return 0.0
    return abs(float(np.percentile(returns, 5))) * 100


def generate_risk_report(
    portfolio: Portfolio,
    position_metadata: dict | None = None,
) -> PortfolioRiskReport:
    """Generate comprehensive risk report.

    Args:
        portfolio: Portfolio with holdings
        position_metadata: Optional dict mapping symbol to
            {conviction, thesis, stop_loss_pct, time_horizon_months, entry_date}
    """
    position_metadata = position_metadata or {}
    total = portfolio.total_current_value
    total_inv = portfolio.total_invested

    # Allocation analysis
    sorted_h = sorted(portfolio.holdings, key=lambda h: -h.current_value)
    top5_val = sum(h.current_value for h in sorted_h[:5])
    top5_pct = (top5_val / total * 100) if total > 0 else 0

    sector_vals: dict[str, float] = {}
    for h in portfolio.holdings:
        sec = h.sector or "Unknown"
        sector_vals[sec] = sector_vals.get(sec, 0) + h.current_value
    sector_pcts = {k: v / total * 100 for k, v in sector_vals.items()} if total > 0 else {}
    sector_max = max(sector_pcts.values(), default=0)

    largest_pct = (sorted_h[0].current_value / total * 100) if sorted_h and total > 0 else 0

    ac_vals: dict[str, float] = {}
    for h in portfolio.holdings:
        ac = h.asset_class.value
        ac_vals[ac] = ac_vals.get(ac, 0) + h.current_value
    ac_breakdown = {k: round(v / total * 100, 1) for k, v in ac_vals.items()} if total > 0 else {}

    # Generate warnings
    warnings = []
    if top5_pct > 70:
        warnings.append(f"CRITICAL: Top 5 positions = {top5_pct:.0f}% — extreme concentration")
    elif top5_pct > 50:
        warnings.append(f"WARNING: Top 5 positions = {top5_pct:.0f}% — high concentration")

    if largest_pct > 25:
        warnings.append(f"CRITICAL: Largest position = {largest_pct:.0f}% — single stock risk")

    if sector_max > 40:
        warnings.append(f"WARNING: Max sector = {sector_max:.0f}% — sector overweight")

    no_thesis = 0
    no_stop_loss = 0
    expired_horizons = 0

    conviction_scores = {"very_high": 5, "high": 4, "medium": 3, "low": 2, "speculative": 1}
    conviction_total = 0
    conviction_count = 0

    position_risks = []
    for h in sorted_h:
        meta = position_metadata.get(h.symbol, {})
        conviction = meta.get("conviction", "medium")
        conviction_total += conviction_scores.get(conviction, 3)
        conviction_count += 1

        if not meta.get("thesis"):
            no_thesis += 1
        if not meta.get("stop_loss_pct"):
            no_stop_loss += 1

        # Check if past time horizon
        entry_date = meta.get("entry_date")
        horizon_months = meta.get("time_horizon_months")
        if entry_date and horizon_months:
            from datetime import timedelta
            target_date = entry_date + timedelta(days=horizon_months * 30)
            if date.today() > target_date:
                expired_horizons += 1
                warnings.append(f"REVIEW: {h.symbol} — past {horizon_months}mo horizon, review thesis")

        alloc_pct = (h.current_value / total * 100) if total > 0 else 0
        position_risks.append(PositionRisk(
            symbol=h.symbol,
            allocation_pct=round(alloc_pct, 2),
            max_drawdown_pct=0,  # requires price history
            beta=0,  # requires price history
            volatility_30d=0,
            conviction=conviction,
            risk_reward=meta.get("risk_reward_ratio", 0),
            position_score=0,
        ))

    if no_thesis > 0:
        warnings.append(f"PROCESS: {no_thesis} positions without documented thesis")
    if no_stop_loss > 0:
        warnings.append(f"RISK: {no_stop_loss} positions without stop-loss defined")

    avg_conv = (conviction_total / conviction_count) if conviction_count > 0 else 3.0

    return PortfolioRiskReport(
        total_value=total,
        total_invested=total_inv,
        top5_concentration_pct=round(top5_pct, 1),
        sector_max_pct=round(sector_max, 1),
        largest_position_pct=round(largest_pct, 1),
        asset_class_breakdown=ac_breakdown,
        portfolio_beta=0,  # requires price history
        max_drawdown_pct=0,
        sharpe_ratio=0,
        sortino_ratio=0,
        var_95_pct=0,
        avg_conviction=round(avg_conv, 1),
        positions_without_thesis=no_thesis,
        positions_without_stop_loss=no_stop_loss,
        expired_time_horizons=expired_horizons,
        warnings=warnings,
        position_risks=position_risks,
    )


# =====================================================================
# Capital Allocation Rules — Enforcing Discipline
# =====================================================================

MAX_SINGLE_POSITION_PCT = 15.0  # No single stock > 15% of portfolio
MAX_SECTOR_PCT = 30.0
MIN_POSITIONS = 8
MAX_POSITIONS = 25
CONVICTION_ALLOCATION = {
    "very_high": 10.0,  # Up to 10% position
    "high": 7.0,
    "medium": 5.0,
    "low": 3.0,
    "speculative": 1.5,
}


def validate_new_position(
    portfolio: Portfolio,
    symbol: str,
    amount: float,
    conviction: str,
    sector: str,
) -> dict:
    """Check if a new position/addition passes allocation rules.

    Returns:
        {"allowed": bool, "warnings": [...], "max_allowed": float}
    """
    total = portfolio.total_current_value + amount
    new_pct = (amount / total * 100) if total > 0 else 100
    warnings = []
    allowed = True

    # Position size check
    max_pct = CONVICTION_ALLOCATION.get(conviction, 5.0)
    if new_pct > max_pct:
        warnings.append(
            f"Position size {new_pct:.1f}% exceeds {max_pct}% limit for {conviction} conviction"
        )
        allowed = False

    if new_pct > MAX_SINGLE_POSITION_PCT:
        warnings.append(f"Position size {new_pct:.1f}% exceeds max {MAX_SINGLE_POSITION_PCT}%")
        allowed = False

    # Sector concentration check
    sector_val = sum(h.current_value for h in portfolio.holdings if h.sector == sector)
    sector_pct = ((sector_val + amount) / total * 100) if total > 0 else 100
    if sector_pct > MAX_SECTOR_PCT:
        warnings.append(f"Sector '{sector}' would be {sector_pct:.1f}% — exceeds {MAX_SECTOR_PCT}%")

    # Position count
    active_count = len([h for h in portfolio.holdings if h.quantity > 0])
    if active_count >= MAX_POSITIONS:
        warnings.append(f"Portfolio already has {active_count} positions (max {MAX_POSITIONS})")

    max_allowed = total * max_pct / 100

    return {
        "allowed": allowed,
        "warnings": warnings,
        "position_pct": round(new_pct, 2),
        "max_allowed_pct": max_pct,
        "max_allowed_amount": round(max_allowed, 0),
        "sector_pct_after": round(sector_pct, 2),
    }
