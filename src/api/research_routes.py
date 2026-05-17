"""Layer 2 API — Research engine endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..collectors.yahoo_collector import YahooCollector
from ..config import get_settings
from ..research.engine import ResearchEngine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/quality/{symbol}")
async def analyze_business_quality(symbol: str):
    """AI-powered business quality analysis."""
    settings = get_settings()
    if not settings.has_openai:
        raise HTTPException(400, "OpenAI API key not configured. Set OPENAI_API_KEY in .env")

    yahoo = YahooCollector()
    fundamentals = yahoo.collect_fundamentals(symbol.upper())
    if not fundamentals:
        raise HTTPException(404, f"No fundamental data for {symbol}")

    engine = ResearchEngine()
    result = engine.analyze_business_quality(symbol.upper(), fundamentals)
    return {"symbol": symbol.upper(), "analysis": result}


@router.get("/risk/{symbol}")
async def analyze_risk_factors(symbol: str):
    """AI-powered risk factor detection."""
    settings = get_settings()
    if not settings.has_openai:
        raise HTTPException(400, "OpenAI API key not configured")

    yahoo = YahooCollector()
    data = {
        "fundamentals": yahoo.collect_fundamentals(symbol.upper()),
        "insider_trades": yahoo.collect_insider_trades(symbol.upper()),
    }

    engine = ResearchEngine()
    result = engine.detect_risk_factors(symbol.upper(), data)
    return {"symbol": symbol.upper(), "risk_analysis": result}


@router.get("/earnings-summary/{symbol}")
async def summarize_earnings(symbol: str):
    """AI-powered earnings report summarization."""
    settings = get_settings()
    if not settings.has_openai:
        raise HTTPException(400, "OpenAI API key not configured")

    yahoo = YahooCollector()
    earnings = yahoo.collect_earnings(symbol.upper())
    fundamentals = yahoo.collect_fundamentals(symbol.upper())

    if not earnings and not fundamentals:
        raise HTTPException(404, f"No earnings data for {symbol}")

    engine = ResearchEngine()
    combined = {"earnings": earnings, "fundamentals": fundamentals}
    result = engine.summarize_earnings(symbol.upper(), combined)
    return {"symbol": symbol.upper(), "earnings_summary": result}


@router.get("/research-note/{symbol}")
async def generate_research_note(symbol: str):
    """Generate a comprehensive AI research note combining all data sources."""
    settings = get_settings()
    if not settings.has_openai:
        raise HTTPException(400, "OpenAI API key not configured")

    yahoo = YahooCollector()
    fundamentals = yahoo.collect_fundamentals(symbol.upper())
    if not fundamentals:
        raise HTTPException(404, f"No data found for {symbol}")

    earnings = yahoo.collect_earnings(symbol.upper())
    insider = yahoo.collect_insider_trades(symbol.upper())

    engine = ResearchEngine()
    result = engine.generate_research_note(
        symbol=symbol.upper(),
        fundamentals=fundamentals,
        earnings=earnings,
        insider=insider,
    )
    return {"symbol": symbol.upper(), "research_note": result}


@router.get("/portfolio-risk")
async def analyze_portfolio_risk():
    """AI-powered portfolio-level risk analysis."""
    settings = get_settings()
    if not settings.has_openai:
        raise HTTPException(400, "OpenAI API key not configured")

    from ..portfolio import load_portfolio
    from ..analyzer import asset_class_allocation, sector_allocation, concentration_risk

    portfolio = load_portfolio()
    portfolio_data = {
        "total_invested": portfolio.total_invested,
        "total_value": portfolio.total_current_value,
        "holdings": [
            {"symbol": h.symbol, "name": h.name, "sector": h.sector,
             "asset_class": h.asset_class.value, "invested": h.invested_amount,
             "current_value": h.current_value, "pnl_pct": h.pnl_percent}
            for h in portfolio.holdings
        ],
        "allocation_by_class": asset_class_allocation(portfolio),
        "allocation_by_sector": sector_allocation(portfolio),
        "concentration": concentration_risk(portfolio),
    }

    engine = ResearchEngine()
    result = engine.analyze_portfolio_risks(portfolio_data)
    return {"portfolio_risk": result}


class CompareQuartersRequest(BaseModel):
    symbol: str
    q1_data: dict
    q2_data: dict


@router.post("/compare-quarters")
async def compare_quarters(req: CompareQuartersRequest):
    """Compare two quarters of financial data."""
    settings = get_settings()
    if not settings.has_openai:
        raise HTTPException(400, "OpenAI API key not configured")

    engine = ResearchEngine()
    result = engine.compare_quarters(req.symbol.upper(), req.q1_data, req.q2_data)
    return {"symbol": req.symbol.upper(), "comparison": result}
