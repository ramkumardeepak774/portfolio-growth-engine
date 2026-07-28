"""Dividend income summary — an aggregation view over existing DIVIDEND
transactions, not a new data concept. TransactionType.DIVIDEND already
exists and is already treated as a cashflow inflow by calculate_xirr(); no
new transaction type or write path is needed for this.

Dividend income is taxed as "income from other sources" at slab rate in
India — a different tax head from src/tax_report.py's STCG/LTCG capital
gains, not part of it.
"""

from __future__ import annotations

from .models import Portfolio, TransactionType
from .tax_report import _parse_fy


def get_dividend_summary(portfolio: Portfolio, fy: str | None = None) -> dict:
    start_year, fy_start, fy_end = _parse_fy(fy)
    fy_label = fy or f"{start_year}-{str(start_year + 1)[2:]}"

    by_holding: dict[str, dict] = {}
    by_month: dict[str, float] = {}
    total = 0.0

    for h in portfolio.holdings:
        for t in h.transactions:
            if t.type != TransactionType.DIVIDEND:
                continue
            if not (fy_start <= t.date <= fy_end):
                continue

            amount = t.quantity * t.price
            total += amount

            entry = by_holding.setdefault(h.symbol, {"symbol": h.symbol, "name": h.name, "total": 0.0, "count": 0})
            entry["total"] += amount
            entry["count"] += 1

            month_key = t.date.strftime("%Y-%m")
            by_month[month_key] = by_month.get(month_key, 0.0) + amount

    return {
        "fy": fy_label,
        "from": fy_start.isoformat(),
        "to": fy_end.isoformat(),
        "total_dividend_income": round(total, 2),
        "by_holding": [
            {"symbol": e["symbol"], "name": e["name"], "total": round(e["total"], 2), "count": e["count"]}
            for e in sorted(by_holding.values(), key=lambda e: -e["total"])
        ],
        "by_month": [
            {"month": month, "total": round(amount, 2)}
            for month, amount in sorted(by_month.items())
        ],
    }
