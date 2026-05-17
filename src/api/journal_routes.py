"""Layer 4 API — Decision journal endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..journal import (
    create_entry,
    get_bias_report,
    get_checklist,
    get_entries_for_symbol,
    get_unreviewed_entries,
    list_entries,
    review_entry,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateEntryRequest(BaseModel):
    symbol: str
    action: str = Field(..., pattern="^(entry|exit|add|trim|hold|watchlist)$")
    why: str = Field(..., min_length=10)
    thesis: str = ""
    assumptions: list[str] = []
    expected_catalyst: str = ""
    risk_factors: list[str] = []
    invalidation_conditions: list[str] = []
    time_horizon: str = ""
    conviction: str = Field("medium", pattern="^(very_high|high|medium|low|speculative)$")
    quantity: float = 0
    price: float = 0
    position_size_pct: float = 0
    tags: list[str] = []


class ReviewEntryRequest(BaseModel):
    outcome: str = Field(..., min_length=5)
    what_went_right: str = ""
    what_went_wrong: str = ""
    bias_identified: str = ""
    lesson_learned: str = ""
    rating: int = Field(0, ge=0, le=10)


@router.post("/entry")
async def create_journal_entry(req: CreateEntryRequest):
    """Create a new decision journal entry.

    IMPORTANT: Document your reasoning BEFORE executing the trade.
    """
    entry = create_entry(
        symbol=req.symbol.upper(),
        action=req.action,
        why=req.why,
        thesis=req.thesis,
        assumptions=req.assumptions,
        expected_catalyst=req.expected_catalyst,
        risk_factors=req.risk_factors,
        invalidation_conditions=req.invalidation_conditions,
        time_horizon=req.time_horizon,
        conviction=req.conviction,
        quantity=req.quantity,
        price=req.price,
        position_size_pct=req.position_size_pct,
        tags=req.tags,
    )
    return {"id": entry.id, "status": "created"}


@router.post("/review/{entry_id}")
async def review_journal_entry(entry_id: str, req: ReviewEntryRequest):
    """Review a past decision — this is how you improve.

    Fill in what went right, what went wrong, and what bias you had.
    Be honest with yourself. This is for you.
    """
    try:
        entry = review_entry(
            entry_id=entry_id,
            outcome=req.outcome,
            what_went_right=req.what_went_right,
            what_went_wrong=req.what_went_wrong,
            bias_identified=req.bias_identified,
            lesson_learned=req.lesson_learned,
            rating=req.rating,
        )
        return {"id": entry.id, "status": "reviewed", "rating": entry.rating}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/entries")
async def get_journal_entries(
    symbol: str | None = None,
    action: str | None = None,
    reviewed: bool | None = None,
    limit: int = 50,
):
    """List journal entries with optional filters."""
    entries = list_entries(symbol=symbol, action=action, reviewed=reviewed, limit=limit)
    return [
        {
            "id": e.id,
            "symbol": e.symbol,
            "action": e.action,
            "date": e.date,
            "why": e.why[:100] + "..." if len(e.why) > 100 else e.why,
            "conviction": e.conviction,
            "is_reviewed": e.is_reviewed,
            "rating": e.rating,
            "tags": e.tags,
        }
        for e in entries
    ]


@router.get("/entries/{symbol}")
async def get_symbol_journal(symbol: str):
    """Get all journal entries for a specific stock."""
    entries = get_entries_for_symbol(symbol.upper())
    return [
        {
            "id": e.id,
            "action": e.action,
            "date": e.date,
            "why": e.why,
            "thesis": e.thesis,
            "conviction": e.conviction,
            "price": e.price,
            "outcome": e.outcome,
            "rating": e.rating,
            "is_reviewed": e.is_reviewed,
        }
        for e in entries
    ]


@router.get("/entry/{entry_id}")
async def get_journal_entry_detail(entry_id: str):
    """Get full details of a journal entry."""
    entries = list_entries(limit=500)
    for e in entries:
        if e.id == entry_id:
            return {
                "id": e.id,
                "symbol": e.symbol,
                "action": e.action,
                "date": e.date,
                "why": e.why,
                "thesis": e.thesis,
                "assumptions": e.assumptions,
                "expected_catalyst": e.expected_catalyst,
                "risk_factors": e.risk_factors,
                "invalidation_conditions": e.invalidation_conditions,
                "time_horizon": e.time_horizon,
                "conviction": e.conviction,
                "quantity": e.quantity,
                "price": e.price,
                "position_size_pct": e.position_size_pct,
                "outcome": e.outcome,
                "what_went_right": e.what_went_right,
                "what_went_wrong": e.what_went_wrong,
                "bias_identified": e.bias_identified,
                "lesson_learned": e.lesson_learned,
                "rating": e.rating,
                "review_date": e.review_date,
                "is_reviewed": e.is_reviewed,
                "tags": e.tags,
            }
    raise HTTPException(404, f"Entry not found: {entry_id}")


@router.get("/unreviewed")
async def get_unreviewed():
    """Get entries that haven't been reviewed yet.

    Review your decisions regularly — this is the fastest way to improve.
    """
    entries = get_unreviewed_entries()
    return {
        "count": len(entries),
        "entries": [
            {"id": e.id, "symbol": e.symbol, "action": e.action, "date": e.date, "why": e.why[:80]}
            for e in entries
        ],
    }


@router.get("/bias-report")
async def get_bias_analysis():
    """Analyze your decision journal for patterns and biases.

    This is how you actually improve as an investor.
    Requires reviewed entries to work.
    """
    return get_bias_report()


@router.get("/checklist/{action}")
async def get_decision_checklist(action: str):
    """Get a pre-decision checklist.

    Forces you to think through the decision before acting.
    Prevents emotional/impulsive trades.
    """
    return {"action": action, "checklist": get_checklist(action)}
