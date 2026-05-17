"""Asset allocation engine — suggests rebalancing to optimize growth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import AssetClass, Portfolio


# --- Target allocation profiles ---

# Aggressive growth (for 1000x target — high equity, high small/mid cap)
AGGRESSIVE_GROWTH = {
    "equity_direct": 40,      # Direct stocks (multi-bagger hunting)
    "mf_small_mid": 25,       # Small & mid cap MFs
    "mf_index_large": 15,     # Index / large cap MFs (stability)
    "mf_international": 5,    # International diversification
    "gold": 5,                # Hedge
    "debt": 5,                # Emergency / stability
    "cash": 5,                # Opportunity fund
}

# Balanced growth
BALANCED_GROWTH = {
    "equity_direct": 25,
    "mf_small_mid": 15,
    "mf_index_large": 25,
    "mf_international": 10,
    "gold": 10,
    "debt": 10,
    "cash": 5,
}

# Conservative
CONSERVATIVE = {
    "equity_direct": 10,
    "mf_small_mid": 5,
    "mf_index_large": 20,
    "mf_international": 5,
    "gold": 15,
    "debt": 35,
    "cash": 10,
}

# Age-based rule: 100 - age = equity %, rest in debt/gold
def age_based_allocation(age: int) -> dict[str, float]:
    equity_pct = max(20, min(90, 100 - age))
    debt_pct = 100 - equity_pct
    return {
        "equity_direct": equity_pct * 0.35,
        "mf_small_mid": equity_pct * 0.25,
        "mf_index_large": equity_pct * 0.25,
        "mf_international": equity_pct * 0.15,
        "gold": debt_pct * 0.3,
        "debt": debt_pct * 0.5,
        "cash": debt_pct * 0.2,
    }


# Map asset classes to allocation buckets
ASSET_CLASS_TO_BUCKET = {
    AssetClass.EQUITY_LARGE_CAP: "equity_direct",
    AssetClass.EQUITY_MID_CAP: "equity_direct",
    AssetClass.EQUITY_SMALL_CAP: "equity_direct",
    AssetClass.EQUITY_MICRO_CAP: "equity_direct",
    AssetClass.MUTUAL_FUND_EQUITY: "mf_small_mid",
    AssetClass.MUTUAL_FUND_HYBRID: "mf_index_large",
    AssetClass.MUTUAL_FUND_DEBT: "debt",
    AssetClass.MUTUAL_FUND_INDEX: "mf_index_large",
    AssetClass.MUTUAL_FUND_ELSS: "mf_small_mid",
    AssetClass.GOLD: "gold",
    AssetClass.FIXED_DEPOSIT: "debt",
    AssetClass.PPF: "debt",
    AssetClass.EPF: "debt",
    AssetClass.NPS: "mf_index_large",
    AssetClass.REAL_ESTATE: "equity_direct",  # illiquid — treat as equity
    AssetClass.CRYPTO: "equity_direct",
    AssetClass.CASH: "cash",
    AssetClass.OTHER: "cash",
}


@dataclass
class RebalanceAction:
    bucket: str
    current_percent: float
    target_percent: float
    diff_percent: float
    current_value: float
    target_value: float
    action: str  # "BUY MORE" or "REDUCE" or "ON TARGET"
    amount: float  # INR to add or remove


def get_current_allocation(portfolio: Portfolio) -> dict[str, float]:
    """Get current allocation by bucket in percentages."""
    total = portfolio.total_current_value
    if total <= 0:
        return {}

    bucket_values: dict[str, float] = {}
    for h in portfolio.holdings:
        bucket = ASSET_CLASS_TO_BUCKET.get(h.asset_class, "cash")
        bucket_values[bucket] = bucket_values.get(bucket, 0) + h.current_value

    return {k: round(v / total * 100, 2) for k, v in bucket_values.items()}


def calculate_rebalance(
    portfolio: Portfolio,
    target: Optional[dict[str, float]] = None,
) -> list[RebalanceAction]:
    """Calculate rebalancing actions to match target allocation.

    Args:
        portfolio: Current portfolio
        target: Target allocation dict (bucket -> percent). Defaults to AGGRESSIVE_GROWTH.

    Returns:
        List of RebalanceAction items.
    """
    if target is None:
        target = AGGRESSIVE_GROWTH

    total = portfolio.total_current_value
    if total <= 0:
        return []

    # Current allocation by bucket (absolute values)
    bucket_values: dict[str, float] = {}
    for h in portfolio.holdings:
        bucket = ASSET_CLASS_TO_BUCKET.get(h.asset_class, "cash")
        bucket_values[bucket] = bucket_values.get(bucket, 0) + h.current_value

    actions = []
    all_buckets = set(list(target.keys()) + list(bucket_values.keys()))

    for bucket in sorted(all_buckets):
        current_val = bucket_values.get(bucket, 0)
        current_pct = (current_val / total * 100) if total > 0 else 0
        target_pct = target.get(bucket, 0)
        diff_pct = target_pct - current_pct
        target_val = total * target_pct / 100
        amount = target_val - current_val

        if abs(diff_pct) < 1.0:
            action_str = "ON TARGET"
        elif diff_pct > 0:
            action_str = "BUY MORE"
        else:
            action_str = "REDUCE"

        actions.append(RebalanceAction(
            bucket=bucket,
            current_percent=round(current_pct, 2),
            target_percent=round(target_pct, 2),
            diff_percent=round(diff_pct, 2),
            current_value=round(current_val, 2),
            target_value=round(target_val, 2),
            action=action_str,
            amount=round(amount, 2),
        ))

    return sorted(actions, key=lambda a: -abs(a.diff_percent))


def suggest_monthly_sip_allocation(
    monthly_amount: float,
    target: Optional[dict[str, float]] = None,
) -> dict[str, float]:
    """Given a monthly SIP amount, split it across buckets per target allocation."""
    if target is None:
        target = AGGRESSIVE_GROWTH

    return {
        bucket: round(monthly_amount * pct / 100, 0)
        for bucket, pct in target.items()
    }
