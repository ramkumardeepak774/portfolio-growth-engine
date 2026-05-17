"""Layer 4 — Decision Journal.

The most important tool for improving as an investor.
Every investment decision is logged with rationale, then reviewed later.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import yaml

from .config import get_settings

logger = logging.getLogger(__name__)

JOURNAL_DIR = Path(__file__).resolve().parent.parent / "data" / "journal"


@dataclass
class JournalEntryData:
    """A single decision journal entry."""
    id: str  # YYYYMMDD_SYMBOL_ACTION
    symbol: str
    action: str  # entry, exit, add, trim, hold, watchlist
    date: str

    # --- Entry Rationale ---
    why: str
    thesis: str = ""
    assumptions: list[str] = field(default_factory=list)
    expected_catalyst: str = ""
    risk_factors: list[str] = field(default_factory=list)
    invalidation_conditions: list[str] = field(default_factory=list)
    time_horizon: str = ""  # "3-5 years"
    conviction: str = "medium"  # very_high, high, medium, low, speculative

    # --- Trade Details ---
    quantity: float = 0
    price: float = 0
    position_size_pct: float = 0

    # --- Review (filled later) ---
    outcome: str = ""
    what_went_right: str = ""
    what_went_wrong: str = ""
    bias_identified: str = ""
    lesson_learned: str = ""
    rating: int = 0  # 1-10 self-grade
    review_date: str = ""
    is_reviewed: bool = False

    tags: list[str] = field(default_factory=list)


def create_entry(
    symbol: str,
    action: str,
    why: str,
    thesis: str = "",
    assumptions: list[str] | None = None,
    expected_catalyst: str = "",
    risk_factors: list[str] | None = None,
    invalidation_conditions: list[str] | None = None,
    time_horizon: str = "",
    conviction: str = "medium",
    quantity: float = 0,
    price: float = 0,
    position_size_pct: float = 0,
    tags: list[str] | None = None,
) -> JournalEntryData:
    """Create a new journal entry."""
    today = date.today()
    entry_id = f"{today.strftime('%Y%m%d')}_{symbol}_{action}"

    entry = JournalEntryData(
        id=entry_id,
        symbol=symbol,
        action=action,
        date=today.isoformat(),
        why=why,
        thesis=thesis,
        assumptions=assumptions or [],
        expected_catalyst=expected_catalyst,
        risk_factors=risk_factors or [],
        invalidation_conditions=invalidation_conditions or [],
        time_horizon=time_horizon,
        conviction=conviction,
        quantity=quantity,
        price=price,
        position_size_pct=position_size_pct,
        tags=tags or [],
    )

    _save_entry(entry)
    logger.info(f"Journal entry created: {entry_id}")
    return entry


def review_entry(
    entry_id: str,
    outcome: str,
    what_went_right: str = "",
    what_went_wrong: str = "",
    bias_identified: str = "",
    lesson_learned: str = "",
    rating: int = 0,
) -> JournalEntryData:
    """Review an existing journal entry — add retrospective analysis."""
    entry = _load_entry(entry_id)
    if entry is None:
        raise ValueError(f"Journal entry not found: {entry_id}")

    entry.outcome = outcome
    entry.what_went_right = what_went_right
    entry.what_went_wrong = what_went_wrong
    entry.bias_identified = bias_identified
    entry.lesson_learned = lesson_learned
    entry.rating = rating
    entry.review_date = date.today().isoformat()
    entry.is_reviewed = True

    _save_entry(entry)
    logger.info(f"Journal entry reviewed: {entry_id}, rating={rating}")
    return entry


def list_entries(
    symbol: str | None = None,
    action: str | None = None,
    reviewed: bool | None = None,
    limit: int = 50,
) -> list[JournalEntryData]:
    """List journal entries with optional filters."""
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    entries = []

    for f in sorted(JOURNAL_DIR.glob("*.yaml"), reverse=True):
        try:
            with open(f) as fh:
                data = yaml.safe_load(fh)
            entry = _dict_to_entry(data)

            if symbol and entry.symbol != symbol:
                continue
            if action and entry.action != action:
                continue
            if reviewed is not None and entry.is_reviewed != reviewed:
                continue

            entries.append(entry)
            if len(entries) >= limit:
                break
        except Exception as e:
            logger.warning(f"Failed to load journal entry {f}: {e}")

    return entries


def get_unreviewed_entries() -> list[JournalEntryData]:
    """Get all entries that haven't been reviewed yet."""
    return list_entries(reviewed=False)


def get_entries_for_symbol(symbol: str) -> list[JournalEntryData]:
    """Get all journal entries for a stock."""
    return list_entries(symbol=symbol)


def get_bias_report() -> dict:
    """Analyze journal for common biases and patterns.

    This is how you actually improve as an investor.
    """
    entries = list_entries(reviewed=True, limit=500)
    if not entries:
        return {"message": "No reviewed entries yet. Review your decisions to see bias analysis."}

    bias_counts: dict[str, int] = {}
    lesson_themes: dict[str, int] = {}
    avg_rating_by_conviction: dict[str, list] = {}
    win_rate_by_action: dict[str, dict] = {}

    for e in entries:
        # Bias tracking
        if e.bias_identified:
            bias = e.bias_identified.lower().strip()
            bias_counts[bias] = bias_counts.get(bias, 0) + 1

        # Conviction vs outcome
        if e.conviction not in avg_rating_by_conviction:
            avg_rating_by_conviction[e.conviction] = []
        if e.rating > 0:
            avg_rating_by_conviction[e.conviction].append(e.rating)

        # Win rate by action type
        if e.action not in win_rate_by_action:
            win_rate_by_action[e.action] = {"total": 0, "good": 0}
        win_rate_by_action[e.action]["total"] += 1
        if e.rating >= 7:
            win_rate_by_action[e.action]["good"] += 1

    return {
        "total_reviewed": len(entries),
        "common_biases": dict(sorted(bias_counts.items(), key=lambda x: -x[1])[:10]),
        "avg_rating_by_conviction": {
            k: round(sum(v) / len(v), 1) if v else 0
            for k, v in avg_rating_by_conviction.items()
        },
        "decision_quality_by_action": {
            k: {
                "total": v["total"],
                "good_decisions_pct": round(v["good"] / v["total"] * 100, 1) if v["total"] > 0 else 0,
            }
            for k, v in win_rate_by_action.items()
        },
        "avg_overall_rating": round(
            sum(e.rating for e in entries if e.rating > 0) / max(1, sum(1 for e in entries if e.rating > 0)),
            1,
        ),
    }


def get_checklist(action: str = "entry") -> list[str]:
    """Return a pre-investment checklist to enforce process.

    Most investors lose because: no process, inconsistent decisions,
    emotional buying, overtrading, poor risk management.
    """
    if action == "entry":
        return [
            "1. THESIS: Can you explain why you're buying in 2-3 sentences?",
            "2. MOAT: What's the competitive advantage? Why can't competitors replicate it?",
            "3. GROWTH: Is revenue/profit growth consistent? What's driving it?",
            "4. VALUATION: Is the price reasonable relative to earnings growth?",
            "5. RISK: What are the top 3 risks? What's the worst case?",
            "6. INVALIDATION: Under what conditions would you sell?",
            "7. POSITION SIZE: Does the allocation match your conviction level?",
            "8. TIME HORIZON: How long are you willing to hold?",
            "9. CATALYST: What will unlock value in the next 6-12 months?",
            "10. BIAS CHECK: Are you buying based on data or FOMO/hype?",
        ]
    elif action == "exit":
        return [
            "1. WHY NOW: What changed? Is the original thesis broken?",
            "2. INVALIDATION: Did any invalidation condition trigger?",
            "3. EMOTIONAL CHECK: Are you selling based on fear or analysis?",
            "4. PARTIAL EXIT: Should you trim instead of fully exiting?",
            "5. TAX: What are the tax implications? (STCG vs LTCG)",
            "6. REDEPLOYMENT: Where will the capital go? Is the alternative better?",
            "7. REVIEW: Document what went right and wrong.",
        ]
    else:
        return [
            "1. WHY: Document your reasoning clearly",
            "2. DATA: Base the decision on data, not emotion",
            "3. SIZE: Is the position size appropriate?",
            "4. REVIEW: Set a date to review this decision",
        ]


# --- Private helpers ---

def _save_entry(entry: JournalEntryData) -> None:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    path = JOURNAL_DIR / f"{entry.id}.yaml"
    data = _entry_to_dict(entry)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def _load_entry(entry_id: str) -> JournalEntryData | None:
    path = JOURNAL_DIR / f"{entry_id}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    return _dict_to_entry(data)


def _entry_to_dict(entry: JournalEntryData) -> dict:
    return {
        "id": entry.id,
        "symbol": entry.symbol,
        "action": entry.action,
        "date": entry.date,
        "why": entry.why,
        "thesis": entry.thesis,
        "assumptions": entry.assumptions,
        "expected_catalyst": entry.expected_catalyst,
        "risk_factors": entry.risk_factors,
        "invalidation_conditions": entry.invalidation_conditions,
        "time_horizon": entry.time_horizon,
        "conviction": entry.conviction,
        "quantity": entry.quantity,
        "price": entry.price,
        "position_size_pct": entry.position_size_pct,
        "outcome": entry.outcome,
        "what_went_right": entry.what_went_right,
        "what_went_wrong": entry.what_went_wrong,
        "bias_identified": entry.bias_identified,
        "lesson_learned": entry.lesson_learned,
        "rating": entry.rating,
        "review_date": entry.review_date,
        "is_reviewed": entry.is_reviewed,
        "tags": entry.tags,
    }


def _dict_to_entry(data: dict) -> JournalEntryData:
    return JournalEntryData(
        id=data["id"],
        symbol=data["symbol"],
        action=data["action"],
        date=data["date"],
        why=data.get("why", ""),
        thesis=data.get("thesis", ""),
        assumptions=data.get("assumptions", []),
        expected_catalyst=data.get("expected_catalyst", ""),
        risk_factors=data.get("risk_factors", []),
        invalidation_conditions=data.get("invalidation_conditions", []),
        time_horizon=data.get("time_horizon", ""),
        conviction=data.get("conviction", "medium"),
        quantity=data.get("quantity", 0),
        price=data.get("price", 0),
        position_size_pct=data.get("position_size_pct", 0),
        outcome=data.get("outcome", ""),
        what_went_right=data.get("what_went_right", ""),
        what_went_wrong=data.get("what_went_wrong", ""),
        bias_identified=data.get("bias_identified", ""),
        lesson_learned=data.get("lesson_learned", ""),
        rating=data.get("rating", 0),
        review_date=data.get("review_date", ""),
        is_reviewed=data.get("is_reviewed", False),
        tags=data.get("tags", []),
    )
