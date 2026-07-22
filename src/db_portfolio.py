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
