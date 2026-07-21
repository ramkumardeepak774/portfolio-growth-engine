"""Layer 3 API — Portfolio decisions and risk management."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..portfolio import load_portfolio
from ..analyzer import (
    asset_class_allocation,
    calculate_portfolio_cagr,
    calculate_portfolio_xirr,
    concentration_risk,
    holding_performance_table,
    portfolio_value_series,
    sector_allocation,
)
from ..allocator import calculate_rebalance, get_current_allocation, suggest_monthly_sip_allocation
from ..decisions import generate_risk_report, validate_new_position
from ..goal_tracker import track_all_goals, growth_scenarios

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary")
async def portfolio_summary():
    """Full portfolio summary with metrics."""
    portfolio = load_portfolio()
    cagr = calculate_portfolio_cagr(portfolio)
    xirr = calculate_portfolio_xirr(portfolio)

    return {
        "total_invested": portfolio.total_invested,
        "total_value": portfolio.total_current_value,
        "total_pnl": portfolio.total_pnl,
        "total_pnl_pct": round(portfolio.total_pnl_percent, 2),
        "cagr": round(cagr, 2),
        "xirr": round(xirr, 2) if xirr else None,
        "holdings_count": len(portfolio.holdings),
    }


@router.get("/holdings")
async def portfolio_holdings():
    """Per-holding performance table."""
    portfolio = load_portfolio()
    df = holding_performance_table(portfolio)
    return df.to_dict(orient="records")


@router.get("/allocation")
async def portfolio_allocation():
    """Asset class and sector allocation breakdown."""
    portfolio = load_portfolio()
    return {
        "by_asset_class": asset_class_allocation(portfolio),
        "by_sector": sector_allocation(portfolio),
        "concentration": concentration_risk(portfolio),
        "current_buckets": get_current_allocation(portfolio),
    }


@router.get("/rebalance")
async def portfolio_rebalance():
    """Rebalancing suggestions."""
    portfolio = load_portfolio()
    actions = calculate_rebalance(portfolio)
    return [
        {
            "bucket": a.bucket,
            "current_pct": a.current_percent,
            "target_pct": a.target_percent,
            "diff_pct": a.diff_percent,
            "action": a.action,
            "amount": a.amount,
        }
        for a in actions
    ]


@router.get("/goals")
async def portfolio_goals():
    """Goal progress tracking."""
    portfolio = load_portfolio()
    goals = track_all_goals(portfolio)
    return [
        {
            "name": gp.goal.name,
            "target_multiplier": gp.goal.target_multiplier,
            "target_years": gp.goal.target_years,
            "current_value": gp.current_value,
            "target_value": gp.target_value,
            "actual_cagr": gp.actual_cagr,
            "required_cagr": gp.required_cagr,
            "required_cagr_from_now": gp.required_cagr_from_now,
            "on_track": gp.on_track,
            "years_remaining": gp.years_remaining,
            "completion_pct": gp.completion_percent,
        }
        for gp in goals
    ]


@router.get("/growth")
async def portfolio_growth(period: str = Query("1y", pattern="^(1mo|3mo|6mo|1y|2y|5y|max)$")):
    """Real weighted portfolio value over time (direct-equity holdings only —
    see analyzer.portfolio_value_series for why mutual funds/gold/etc. are excluded)."""
    portfolio = load_portfolio()
    series = portfolio_value_series(portfolio, period=period)
    return {"period": period, "series": series}


@router.get("/risk-report")
async def portfolio_risk_report():
    """Comprehensive portfolio risk dashboard."""
    portfolio = load_portfolio()
    report = generate_risk_report(portfolio)
    return {
        "total_value": report.total_value,
        "top5_concentration_pct": report.top5_concentration_pct,
        "sector_max_pct": report.sector_max_pct,
        "largest_position_pct": report.largest_position_pct,
        "asset_class_breakdown": report.asset_class_breakdown,
        "avg_conviction": report.avg_conviction,
        "positions_without_thesis": report.positions_without_thesis,
        "positions_without_stop_loss": report.positions_without_stop_loss,
        "warnings": report.warnings,
        "position_risks": [
            {
                "symbol": pr.symbol,
                "allocation_pct": pr.allocation_pct,
                "conviction": pr.conviction,
            }
            for pr in report.position_risks
        ],
    }


class NewPositionCheck(BaseModel):
    symbol: str
    amount: float
    conviction: str = "medium"
    sector: str = "Unknown"


@router.post("/check-position")
async def check_new_position(req: NewPositionCheck):
    """Validate a new position against allocation rules."""
    portfolio = load_portfolio()
    result = validate_new_position(
        portfolio, req.symbol.upper(), req.amount, req.conviction, req.sector
    )
    return result


@router.get("/sip-allocation/{amount}")
async def sip_allocation(amount: float):
    """How to split a monthly SIP amount."""
    alloc = suggest_monthly_sip_allocation(amount)
    return {"monthly_amount": amount, "allocation": alloc}


@router.get("/growth-scenarios")
async def get_growth_scenarios(initial: float | None = None):
    """Growth projections at various CAGR rates."""
    portfolio = load_portfolio()
    corpus = initial or portfolio.total_invested
    return {"initial_corpus": corpus, "scenarios": growth_scenarios(corpus)}
