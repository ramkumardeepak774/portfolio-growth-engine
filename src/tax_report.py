"""Capital gains (STCG/LTCG) report for equity/equity-MF holdings.

Scope (deliberately limited — see BACKLOG/roadmap discussion):
  - Equity and equity-mutual-fund holdings only. Gold, hybrid/index/debt
    funds, FD/PPF/EPF/NPS, real estate, crypto, and cash have materially
    different (or holding-dependent) tax treatment this app doesn't track —
    they're listed under `unsupported_asset_classes` in the response rather
    than silently included or excluded.
  - FIFO lot matching (matches Zerodha's own Tax P&L report convention).
  - Long-term threshold: >=12 calendar months held (via relativedelta, not
    a flat 365-day count — a 12-month holding spanning a leap-year Feb is
    still 12 months, not 366+ days).
  - Gain amounts only, not an estimated tax payable — equity STCG/LTCG
    rates changed mid financial-year-2024-25 (Budget, 23 Jul 2024), so a
    single flat rate can't be applied uniformly within one FY.
  - Ignores brokerage/charges in the gain calculation (price-only) — the
    existing Transaction.amount property already conflates charges into
    both buy and sell amounts in a way that would double up here.
  - Out of scope entirely: Section 112A grandfathering (special cost basis
    for equity LTCG bought before 31 Jan 2018), and dividend income (a
    different tax head — income from other sources, not capital gains).

This is informational only and not a substitute for professional tax
advice — the tax rules implemented here are a simplification and haven't
been reviewed by a tax professional.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from dateutil.relativedelta import relativedelta

from .models import AssetClass, Holding, Portfolio, TransactionType

EQUITY_ASSET_CLASSES = {
    AssetClass.EQUITY_LARGE_CAP,
    AssetClass.EQUITY_MID_CAP,
    AssetClass.EQUITY_SMALL_CAP,
    AssetClass.EQUITY_MICRO_CAP,
    AssetClass.MUTUAL_FUND_EQUITY,
    AssetClass.MUTUAL_FUND_ELSS,
}

_LONG_TERM_MONTHS = 12


@dataclass
class RealizedLot:
    symbol: str
    buy_date: date
    sell_date: date
    quantity: float
    buy_price: float
    sell_price: float
    gain: float
    term: str  # "stcg" | "ltcg"


class InvalidFinancialYear(ValueError):
    pass


def _parse_fy(fy: str | None) -> tuple[int, date, date]:
    """Returns (start_year, fy_start, fy_end) for e.g. "2024-25" -> (2024, 2024-04-01, 2025-03-31)."""
    if fy is None:
        today = date.today()
        start_year = today.year if today.month >= 4 else today.year - 1
    else:
        parts = fy.split("-")
        if len(parts) != 2 or not parts[0].isdigit():
            raise InvalidFinancialYear(f"Invalid FY format: {fy!r}, expected e.g. '2024-25'")
        start_year = int(parts[0])
    return start_year, date(start_year, 4, 1), date(start_year + 1, 3, 31)


def _fifo_realized_lots(holding: Holding) -> list[RealizedLot]:
    """Match SELL transactions against earlier BUY/SIP lots, FIFO.

    Only BUY/SIP (inflow) and SELL (outflow) affect lots — DIVIDEND/SWITCH
    are ignored here, consistent with how Holding.quantity/invested_amount
    already treat them elsewhere in this codebase.
    """
    open_lots: list[dict] = []  # [{"date": date, "qty": float, "price": float}]
    realized: list[RealizedLot] = []

    for t in sorted(holding.transactions, key=lambda t: t.date):
        if t.type in (TransactionType.BUY, TransactionType.SIP):
            open_lots.append({"date": t.date, "qty": t.quantity, "price": t.price})
        elif t.type == TransactionType.SELL:
            remaining = t.quantity
            while remaining > 1e-9 and open_lots:
                lot = open_lots[0]
                matched_qty = min(lot["qty"], remaining)
                months_held = relativedelta(t.date, lot["date"])
                total_months = months_held.years * 12 + months_held.months
                term = "ltcg" if total_months >= _LONG_TERM_MONTHS else "stcg"
                realized.append(
                    RealizedLot(
                        symbol=holding.symbol,
                        buy_date=lot["date"],
                        sell_date=t.date,
                        quantity=matched_qty,
                        buy_price=lot["price"],
                        sell_price=t.price,
                        gain=matched_qty * (t.price - lot["price"]),
                        term=term,
                    )
                )
                lot["qty"] -= matched_qty
                remaining -= matched_qty
                if lot["qty"] <= 1e-9:
                    open_lots.pop(0)
            # If remaining > 0 here, the holding was oversold relative to
            # recorded buys (a data-entry issue upstream) — nothing more to
            # match against; the unmatched portion is silently dropped
            # rather than crashing the whole report.

    return realized


def _serialize_lot(lot: RealizedLot) -> dict:
    return {
        "symbol": lot.symbol,
        "buy_date": lot.buy_date.isoformat(),
        "sell_date": lot.sell_date.isoformat(),
        "quantity": round(lot.quantity, 4),
        "buy_price": round(lot.buy_price, 2),
        "sell_price": round(lot.sell_price, 2),
        "gain": round(lot.gain, 2),
    }


def generate_tax_report(portfolio: Portfolio, fy: str | None = None) -> dict:
    start_year, fy_start, fy_end = _parse_fy(fy)
    fy_label = fy or f"{start_year}-{str(start_year + 1)[2:]}"

    stcg_lots: list[RealizedLot] = []
    ltcg_lots: list[RealizedLot] = []
    unsupported: dict[str, set[str]] = {}

    for h in portfolio.holdings:
        if h.asset_class not in EQUITY_ASSET_CLASSES:
            if h.transactions:
                unsupported.setdefault(h.asset_class.value, set()).add(h.symbol)
            continue
        for lot in _fifo_realized_lots(h):
            if not (fy_start <= lot.sell_date <= fy_end):
                continue
            (stcg_lots if lot.term == "stcg" else ltcg_lots).append(lot)

    return {
        "fy": fy_label,
        "from": fy_start.isoformat(),
        "to": fy_end.isoformat(),
        "stcg": {
            "total_gain": round(sum(lot.gain for lot in stcg_lots), 2),
            "lots": [_serialize_lot(lot) for lot in stcg_lots],
        },
        "ltcg": {
            "total_gain": round(sum(lot.gain for lot in ltcg_lots), 2),
            "lots": [_serialize_lot(lot) for lot in ltcg_lots],
        },
        "unsupported_asset_classes": [
            {
                "asset_class": ac,
                "symbols": sorted(symbols),
                "note": "Not yet supported — tax treatment for this asset class isn't implemented.",
            }
            for ac, symbols in sorted(unsupported.items())
        ],
    }
