"""Import holdings from a Zerodha Kite "Holdings" CSV export
(Console → Portfolio → Holdings → Download).

This is a current-snapshot export (quantity, average cost, LTP) — it has no
individual trade dates or history, unlike a Tradebook export. So each row
becomes a single synthetic "buy" transaction dated today, using average
cost as the price. This gets the current value/P&L right immediately (LTP
sets current_price directly) but CAGR/XIRR since-inception will read as
near-zero until real transaction history is added — there's no way around
that with only a snapshot to work from.

For symbols that aren't already a holding, asset_class/name are inferred
with simple heuristics and flagged in the response for the user to review —
there's no "edit holding" UI yet to fix a wrong guess in-app.
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import date

from .db.engine import get_sync_session_factory
from .db.models import Stock

logger = logging.getLogger(__name__)
from .db_portfolio import PortfolioWriteError, add_transaction

REQUIRED_COLUMNS = {"Instrument", "Qty.", "Avg. cost", "LTP"}


@dataclass
class ImportRow:
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    is_new_holding: bool
    inferred_name: str | None = None
    inferred_asset_class: str | None = None


@dataclass
class ImportError_:
    row: int
    symbol: str
    message: str


@dataclass
class ImportResult:
    rows: list[ImportRow]
    errors: list[ImportError_]

    @property
    def new_symbols(self) -> list[str]:
        return [r.symbol for r in self.rows if r.is_new_holding]


def _infer_asset_class(name: str) -> str:
    upper = name.upper()
    if "ELSS" in upper:
        return "mf_elss"
    if "FUND" in upper:
        return "mf_equity"
    if "GOLD" in upper:
        return "gold"
    if "SILVER" in upper:
        return "gold"  # closest bucket we have — flagged for review either way
    return "equity_large_cap"  # direct stocks, ETFs, index products trading like a stock


def _existing_symbols() -> set[str]:
    session_factory = get_sync_session_factory()
    with session_factory() as session:
        return {s.symbol for s in session.query(Stock.symbol).all()}


def parse_holdings_csv(csv_text: str) -> ImportResult:
    """Parse the CSV and classify each row — doesn't touch the DB except to
    read existing symbols (to know what's new vs. an existing holding)."""
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
        raise PortfolioWriteError(
            f"CSV is missing expected columns. Need at least: {', '.join(sorted(REQUIRED_COLUMNS))}"
        )

    existing = _existing_symbols()
    rows: list[ImportRow] = []
    errors: list[ImportError_] = []

    for i, raw in enumerate(reader, start=2):  # row 1 is the header
        symbol = (raw.get("Instrument") or "").strip().upper()
        if not symbol:
            continue
        try:
            quantity = float(raw["Qty."])
            avg_cost = float(raw["Avg. cost"])
            ltp = float(raw["LTP"])
        except (ValueError, KeyError) as e:
            errors.append(ImportError_(row=i, symbol=symbol, message=f"Could not parse numeric fields: {e}"))
            continue

        is_new = symbol not in existing
        rows.append(
            ImportRow(
                symbol=symbol,
                quantity=quantity,
                avg_cost=avg_cost,
                current_price=ltp,
                is_new_holding=is_new,
                inferred_name=symbol if is_new else None,
                inferred_asset_class=_infer_asset_class(symbol) if is_new else None,
            )
        )
        if is_new:
            existing.add(symbol)  # avoid re-flagging the same new symbol twice within one file

    return ImportResult(rows=rows, errors=errors)


def commit_import(csv_text: str) -> ImportResult:
    """Parse and actually write every row via add_transaction()."""
    result = parse_holdings_csv(csv_text)
    today = date.today()

    for row in result.rows:
        try:
            add_transaction(
                symbol=row.symbol,
                txn_type="buy",
                txn_date=today,
                quantity=row.quantity,
                price=row.avg_cost,
                current_price=row.current_price,
                name=row.inferred_name,
                asset_class=row.inferred_asset_class,
            )
        except PortfolioWriteError as e:
            result.errors.append(ImportError_(row=0, symbol=row.symbol, message=str(e)))
        except Exception as e:
            # A DB-level failure (e.g. a value too long for a column) on
            # one row must not silently abort the rest of the batch and
            # leave a partial, hard-to-diagnose import — collect it and
            # keep going, same as a validation error.
            logger.exception("Unexpected error importing %s", row.symbol)
            result.errors.append(ImportError_(row=0, symbol=row.symbol, message=str(e)))

    result.rows = [r for r in result.rows if r.symbol not in {e.symbol for e in result.errors}]
    return result
