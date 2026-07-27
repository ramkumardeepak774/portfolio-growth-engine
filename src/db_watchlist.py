"""Postgres-backed watchlist storage.

A watchlist entry tracks a symbol the user is considering buying — no
Position, no Transaction, no cost basis. Reuses the Stock table for
symbol/name/asset_class/sector, same as holdings do.
"""

from __future__ import annotations

from .db.engine import get_sync_session_factory
from .db.models import AssetClassEnum, Stock
from .db.models import WatchlistItem as DBWatchlistItem
from .db_portfolio import PortfolioWriteError


class WatchlistItemNotFoundError(Exception):
    """Raised when a symbol isn't on the watchlist."""


def add_to_watchlist(
    symbol: str,
    *,
    name: str | None = None,
    asset_class: str | None = None,
    sector: str | None = None,
    target_price: float | None = None,
    notes: str | None = None,
) -> None:
    """Add a symbol to the watchlist, creating the Stock if it's new.

    If the symbol is already on the watchlist, updates target_price/notes
    (whichever were provided) instead of erroring — same idempotent-add
    shape as add_transaction()'s reactivation of an inactive position.
    """
    symbol = symbol.upper().strip()
    session_factory = get_sync_session_factory()
    with session_factory() as session:
        stock = session.query(Stock).filter_by(symbol=symbol).one_or_none()

        if stock is None:
            if not name or not asset_class:
                raise PortfolioWriteError(
                    f"'{symbol}' is a new symbol — name and asset_class are required"
                )
            try:
                asset_class_enum = AssetClassEnum(asset_class)
            except ValueError:
                raise PortfolioWriteError(f"Invalid asset class: {asset_class!r}")
            stock = Stock(symbol=symbol, name=name, asset_class=asset_class_enum, sector=sector)
            session.add(stock)
            session.flush()

        item = session.query(DBWatchlistItem).filter_by(stock_id=stock.id).one_or_none()
        if item is None:
            item = DBWatchlistItem(stock_id=stock.id, target_price=target_price, notes=notes)
            session.add(item)
        else:
            if target_price is not None:
                item.target_price = target_price
            if notes is not None:
                item.notes = notes

        session.commit()


def remove_from_watchlist(symbol: str) -> None:
    symbol = symbol.upper().strip()
    session_factory = get_sync_session_factory()
    with session_factory() as session:
        stock = session.query(Stock).filter_by(symbol=symbol).one_or_none()
        item = (
            session.query(DBWatchlistItem).filter_by(stock_id=stock.id).one_or_none()
            if stock is not None
            else None
        )
        if item is None:
            raise WatchlistItemNotFoundError(f"'{symbol}' is not on the watchlist")

        session.delete(item)
        session.commit()


def get_watchlist() -> list[dict]:
    """Watchlist entries without live price — the API route fetches that
    separately since it needs to offload blocking yfinance calls."""
    session_factory = get_sync_session_factory()
    with session_factory() as session:
        items = session.query(DBWatchlistItem).order_by(DBWatchlistItem.added_at).all()
        return [
            {
                "symbol": item.stock.symbol,
                "name": item.stock.name,
                "asset_class": item.stock.asset_class.value,
                "sector": item.stock.sector,
                "target_price": item.target_price,
                "notes": item.notes,
                "added_at": item.added_at,
            }
            for item in items
        ]
