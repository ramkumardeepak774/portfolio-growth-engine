"""Postgres-backed portfolio storage.

Holdings/transactions live in Neon (Stock/Position/Transaction tables,
previously unused) instead of data/portfolio.yaml — Railway's container
filesystem is ephemeral, so anything written to that file would vanish on
the next deploy.

Reads are DB-first with a YAML fallback (via portfolio.load_portfolio) for
resilience and so the existing test suite / local dev without a DATABASE_URL
keep working unchanged. Writes go straight to Postgres — no fallback, since
silently "succeeding" a write that didn't persist would be actively wrong.
"""

from __future__ import annotations

import logging
from datetime import date as date_type

from .db.engine import get_sync_session_factory
from .db.models import AssetClassEnum, Position, Stock
from .db.models import Transaction as DBTransaction
from .db.models import TxnType
from .models import AssetClass, Holding, Portfolio, Transaction, TransactionType

logger = logging.getLogger(__name__)


class PortfolioWriteError(Exception):
    """Raised for invalid writes (e.g. missing fields for a brand-new holding)."""


class TransactionNotFoundError(Exception):
    """Raised when a transaction id doesn't exist."""


class HoldingNotFoundError(Exception):
    """Raised when a symbol has no holding (Stock/Position) at all."""


def load_portfolio_from_db() -> Portfolio:
    """Reconstruct the Portfolio dataclass from Postgres — raises on any DB error."""
    session_factory = get_sync_session_factory()
    with session_factory() as session:
        positions = session.query(Position).filter_by(is_active=True).all()
        holdings = []
        for pos in positions:
            stock = pos.stock
            transactions = [
                Transaction(
                    date=t.date,
                    type=TransactionType(t.txn_type.value),
                    quantity=t.quantity,
                    price=t.price,
                    charges=t.charges,
                    id=t.id,
                )
                for t in sorted(pos.transactions, key=lambda t: t.date)
            ]
            holdings.append(
                Holding(
                    symbol=stock.symbol,
                    name=stock.name,
                    asset_class=AssetClass(stock.asset_class.value),
                    transactions=transactions,
                    current_price=pos.current_price,
                    sector=stock.sector,
                    notes=pos.notes,
                )
            )
        return Portfolio(holdings=holdings)


def get_portfolio() -> Portfolio:
    """DB-first, YAML-fallback (see module docstring). Goals stay YAML-only for now."""
    from .portfolio import load_portfolio as load_portfolio_from_yaml

    try:
        db_portfolio = load_portfolio_from_db()
    except Exception:
        logger.warning("Could not load portfolio from DB, falling back to YAML", exc_info=True)
        return load_portfolio_from_yaml()

    if not db_portfolio.holdings:
        # DB reachable but empty — most likely not seeded yet. Fall back
        # rather than show an empty dashboard.
        return load_portfolio_from_yaml()

    db_portfolio.goals = load_portfolio_from_yaml().goals
    return db_portfolio


def add_transaction(
    *,
    symbol: str,
    txn_type: str,
    txn_date: date_type,
    quantity: float,
    price: float,
    charges: float = 0.0,
    name: str | None = None,
    asset_class: str | None = None,
    sector: str | None = None,
    current_price: float | None = None,
) -> None:
    """Record a transaction, creating the Stock/Position if this is a new holding.

    `current_price`, if given, updates Position.current_price (e.g. from a
    broker export's LTP column) — otherwise it's left as whatever it was.
    """
    symbol = symbol.upper().strip()
    try:
        parsed_type = TxnType(txn_type)
    except ValueError:
        raise PortfolioWriteError(f"Invalid transaction type: {txn_type!r}")

    session_factory = get_sync_session_factory()
    with session_factory() as session:
        stock = session.query(Stock).filter_by(symbol=symbol).one_or_none()

        if stock is None:
            if not name or not asset_class:
                raise PortfolioWriteError(
                    f"'{symbol}' is a new holding — name and asset_class are required"
                )
            try:
                asset_class_enum = AssetClassEnum(asset_class)
            except ValueError:
                raise PortfolioWriteError(f"Invalid asset class: {asset_class!r}")
            stock = Stock(symbol=symbol, name=name, asset_class=asset_class_enum, sector=sector)
            session.add(stock)
            session.flush()

        position = session.query(Position).filter_by(stock_id=stock.id).one_or_none()
        if position is None:
            position = Position(stock_id=stock.id, is_active=True)
            session.add(position)
            session.flush()
        elif not position.is_active:
            position.is_active = True

        if current_price is not None:
            position.current_price = current_price

        amount = quantity * price + charges
        session.add(
            DBTransaction(
                position_id=position.id,
                txn_type=parsed_type,
                date=txn_date,
                quantity=quantity,
                price=price,
                charges=charges,
                amount=amount,
            )
        )
        session.commit()


class _SimTxn:
    """Lightweight stand-in for a hypothetical edited transaction — only
    the fields _running_quantity_goes_negative() needs to forward-simulate."""

    def __init__(self, date: date_type, txn_type: TxnType, quantity: float):
        self.date = date
        self.txn_type = txn_type
        self.quantity = quantity


def _running_quantity_goes_negative(
    position: Position, *, excluding_id: int, hypothetical: "_SimTxn | None"
) -> bool:
    """Forward-simulate the position's running quantity across all its
    transactions (in date order), with `excluding_id` removed and
    `hypothetical` substituted in its place (None for a delete). Returns
    True if quantity would ever go negative — used to block an edit/delete
    that would silently corrupt CAGR/XIRR/holdings math downstream."""
    txns = [t for t in position.transactions if t.id != excluding_id]
    if hypothetical is not None:
        txns.append(hypothetical)

    qty = 0.0
    for t in sorted(txns, key=lambda t: t.date):
        if t.txn_type in (TxnType.BUY, TxnType.SIP):
            qty += t.quantity
        elif t.txn_type == TxnType.SELL:
            qty -= t.quantity
        if qty < -1e-9:
            return True
    return False


def update_transaction(
    transaction_id: int,
    *,
    txn_type: str | None = None,
    txn_date: date_type | None = None,
    quantity: float | None = None,
    price: float | None = None,
    charges: float | None = None,
) -> None:
    """Edit a transaction's fields. Only provided (non-None) fields change.

    Rejects (PortfolioWriteError) an edit that would drive the holding's
    running quantity negative — e.g. shrinking an early BUY that a later
    SELL depends on.
    """
    session_factory = get_sync_session_factory()
    with session_factory() as session:
        txn = session.get(DBTransaction, transaction_id)
        if txn is None:
            raise TransactionNotFoundError(f"No transaction with id {transaction_id}")

        new_type = txn.txn_type
        if txn_type is not None:
            try:
                new_type = TxnType(txn_type)
            except ValueError:
                raise PortfolioWriteError(f"Invalid transaction type: {txn_type!r}")
        new_date = txn_date if txn_date is not None else txn.date
        new_quantity = quantity if quantity is not None else txn.quantity
        new_price = price if price is not None else txn.price
        new_charges = charges if charges is not None else txn.charges

        position = session.get(Position, txn.position_id)
        hypothetical = _SimTxn(date=new_date, txn_type=new_type, quantity=new_quantity)
        if _running_quantity_goes_negative(position, excluding_id=txn.id, hypothetical=hypothetical):
            raise PortfolioWriteError(
                f"This edit would make {position.stock.symbol}'s quantity go negative "
                "— check the transaction history for this holding."
            )

        txn.txn_type = new_type
        txn.date = new_date
        txn.quantity = new_quantity
        txn.price = new_price
        txn.charges = new_charges
        txn.amount = new_quantity * new_price + new_charges
        session.commit()


def delete_transaction(transaction_id: int) -> None:
    """Delete a transaction. Rejects (PortfolioWriteError) a delete that
    would drive the holding's running quantity negative — does not touch
    Position.is_active, that's a separate explicit "delete holding" action.
    """
    session_factory = get_sync_session_factory()
    with session_factory() as session:
        txn = session.get(DBTransaction, transaction_id)
        if txn is None:
            raise TransactionNotFoundError(f"No transaction with id {transaction_id}")

        position = session.get(Position, txn.position_id)
        if _running_quantity_goes_negative(position, excluding_id=txn.id, hypothetical=None):
            raise PortfolioWriteError(
                f"Deleting this transaction would make {position.stock.symbol}'s "
                "quantity go negative — check the transaction history for this holding."
            )

        session.delete(txn)
        session.commit()


def update_holding(
    symbol: str,
    *,
    name: str | None = None,
    asset_class: str | None = None,
    sector: str | None = None,
    notes: str | None = None,
) -> None:
    """Edit a holding's name/asset_class/sector/notes. Only provided fields
    change. Changing asset_class is a real reclassification — it affects
    the tax report's equity-bucket test and portfolio_value_series'
    priceability, not just cosmetic display.
    """
    symbol = symbol.upper().strip()
    session_factory = get_sync_session_factory()
    with session_factory() as session:
        stock = session.query(Stock).filter_by(symbol=symbol).one_or_none()
        if stock is None:
            raise HoldingNotFoundError(f"No holding for symbol {symbol!r}")

        if name is not None:
            stock.name = name
        if asset_class is not None:
            try:
                stock.asset_class = AssetClassEnum(asset_class)
            except ValueError:
                raise PortfolioWriteError(f"Invalid asset class: {asset_class!r}")
        if sector is not None:
            stock.sector = sector

        if notes is not None:
            position = session.query(Position).filter_by(stock_id=stock.id).one_or_none()
            if position is not None:
                position.notes = notes

        session.commit()


def deactivate_holding(symbol: str) -> None:
    """Soft-delete a holding (Position.is_active = False) — idempotent,
    deactivating an already-inactive holding is a no-op, not an error.
    Adding a new transaction for the symbol later reactivates it
    (existing behavior in add_transaction), so this isn't permanent.
    """
    symbol = symbol.upper().strip()
    session_factory = get_sync_session_factory()
    with session_factory() as session:
        stock = session.query(Stock).filter_by(symbol=symbol).one_or_none()
        if stock is None:
            raise HoldingNotFoundError(f"No holding for symbol {symbol!r}")

        position = session.query(Position).filter_by(stock_id=stock.id).one_or_none()
        if position is None:
            raise HoldingNotFoundError(f"No holding for symbol {symbol!r}")

        position.is_active = False
        session.commit()
