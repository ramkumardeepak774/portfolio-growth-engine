"""Goal tracking — are you on track for 1000x?"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

import numpy as np

from .analyzer import calculate_portfolio_cagr, calculate_portfolio_xirr
from .models import Goal, Portfolio


@dataclass
class GoalProgress:
    goal: Goal
    current_value: float
    actual_cagr: float
    required_cagr: float
    required_cagr_from_now: float  # CAGR needed from today to reach target
    on_track: bool
    projected_value_at_target: float  # if current CAGR continues
    target_value: float
    years_elapsed: float
    years_remaining: float
    completion_percent: float  # how far toward target (log scale)


def _future_value(present: float, rate_pct: float, years: float) -> float:
    """Calculate future value given annual rate."""
    if years <= 0:
        return present
    return present * (1 + rate_pct / 100) ** years


def _required_cagr_from_now(current: float, target: float, years: float) -> float:
    """CAGR needed from current value to reach target in remaining years."""
    if current <= 0 or years <= 0:
        return float("inf")
    return ((target / current) ** (1 / years) - 1) * 100


def track_goal(portfolio: Portfolio, goal: Goal) -> GoalProgress:
    """Evaluate progress toward a single goal."""
    current_value = portfolio.total_current_value
    target_value = goal.target_corpus
    years_elapsed = goal.years_elapsed
    years_remaining = goal.years_remaining

    # Actual performance
    actual_cagr = calculate_portfolio_cagr(portfolio)

    # What's needed from the start vs from now
    required_cagr = goal.required_cagr
    required_from_now = _required_cagr_from_now(current_value, target_value, years_remaining)

    # Project where we'll be if current CAGR continues
    projected = _future_value(current_value, actual_cagr, years_remaining) if actual_cagr > 0 else current_value

    # On-track check: is actual CAGR >= required, or is projected >= target
    on_track = projected >= target_value

    # Completion on log scale (1000x = 3 on log10, so current log10(multiplier) / 3)
    if goal.initial_corpus > 0 and current_value > 0:
        current_multiplier = current_value / goal.initial_corpus
        target_log = np.log10(goal.target_multiplier)
        current_log = np.log10(max(current_multiplier, 1))
        completion_pct = min(100, (current_log / target_log) * 100) if target_log > 0 else 0
    else:
        completion_pct = 0

    return GoalProgress(
        goal=goal,
        current_value=current_value,
        actual_cagr=round(actual_cagr, 2),
        required_cagr=round(required_cagr, 2),
        required_cagr_from_now=round(required_from_now, 2),
        on_track=on_track,
        projected_value_at_target=round(projected, 2),
        target_value=round(target_value, 2),
        years_elapsed=round(years_elapsed, 1),
        years_remaining=round(years_remaining, 1),
        completion_percent=round(completion_pct, 2),
    )


def track_all_goals(portfolio: Portfolio) -> list[GoalProgress]:
    """Track progress for all goals."""
    return [track_goal(portfolio, g) for g in portfolio.goals]


def milestone_table(goal: Goal) -> list[dict]:
    """Show milestone checkpoints for a goal.

    E.g., for 1000x in 20 years at ~41.4% CAGR:
    Year 5  → ~4x
    Year 10 → ~31x
    Year 15 → ~177x
    Year 20 → ~1000x
    """
    cagr = goal.required_cagr / 100
    milestones = []
    for year in range(1, goal.target_years + 1):
        multiplier = (1 + cagr) ** year
        value = goal.initial_corpus * multiplier
        milestones.append({
            "year": year,
            "date": date(goal.start_date.year + year, goal.start_date.month, goal.start_date.day),
            "multiplier": round(multiplier, 1),
            "projected_value": round(value, 0),
        })
    return milestones


def growth_scenarios(initial: float, years: int = 20) -> list[dict]:
    """Show what different CAGR rates produce over time."""
    rates = [12, 15, 20, 25, 30, 35, 40, 50]
    scenarios = []
    for r in rates:
        final = initial * (1 + r / 100) ** years
        multiplier = final / initial
        scenarios.append({
            "cagr_percent": r,
            "final_value": round(final, 0),
            "multiplier": round(multiplier, 1),
        })
    return scenarios
