"""Postgres-backed historical price cache, backed by Yahoo Finance.

Falls back to a live Yahoo Finance fetch (uncached) whenever Postgres is
unreachable or misconfigured — a stale/missing cache should never take the
dashboard down.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .db.engine import get_sync_session_factory
from .db.models import AssetClassEnum, DataSource, PriceHistory, Stock
from .market_data import fetch_historical_prices
from .models import AssetClass

logger = logging.getLogger(__name__)

_PERIOD_DAYS = {
    "1mo": 31,
    "3mo": 93,
    "6mo": 186,
    "1y": 366,
    "2y": 731,
    "5y": 1827,
    "max": 20000,
}


def get_price_history(symbol: str, asset_class: AssetClass, period: str = "1y") -> pd.DataFrame:
    """Return a DataFrame with Date/Close columns, using the Postgres cache when fresh."""
    try:
        return _get_price_history_cached(symbol, asset_class, period)
    except Exception:
        logger.warning("Price cache unavailable for %s, falling back to live fetch", symbol, exc_info=True)
        return _fetch_live(symbol, asset_class, period)


def _get_price_history_cached(symbol: str, asset_class: AssetClass, period: str) -> pd.DataFrame:
    session_factory = get_sync_session_factory()
    period_start = date.today() - timedelta(days=_PERIOD_DAYS.get(period, 366))

    with session_factory() as session:
        stock = session.query(Stock).filter_by(symbol=symbol).one_or_none()

        if stock is not None:
            cached = (
                session.query(PriceHistory)
                .filter(PriceHistory.stock_id == stock.id, PriceHistory.date >= period_start)
                .order_by(PriceHistory.date)
                .all()
            )
            if cached and _is_fresh(cached, period_start):
                return pd.DataFrame({"Date": [c.date for c in cached], "Close": [c.close for c in cached]})

        hist = fetch_historical_prices(symbol, asset_class, period=period)
        if hist is None or hist.empty:
            return pd.DataFrame(columns=["Date", "Close"])

        if stock is None:
            stock = Stock(symbol=symbol, name=symbol, asset_class=AssetClassEnum(asset_class.value))
            session.add(stock)
            session.flush()

        # Single bulk upsert instead of one query + insert/update per row —
        # the earlier row-by-row version took ~80s per holding over Neon's
        # network round trip.
        rows = []
        for idx, row in hist.iterrows():
            row_date = idx.date() if hasattr(idx, "date") else idx
            close = float(row["Close"])
            rows.append(
                {
                    "stock_id": stock.id,
                    "date": row_date,
                    "open": float(row.get("Open", close)),
                    "high": float(row.get("High", close)),
                    "low": float(row.get("Low", close)),
                    "close": close,
                    "volume": int(row.get("Volume") or 0),
                    "source": DataSource.YAHOO,
                }
            )
        if rows:
            stmt = pg_insert(PriceHistory).values(rows)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_price_stock_date",
                set_={"close": stmt.excluded.close, "open": stmt.excluded.open,
                      "high": stmt.excluded.high, "low": stmt.excluded.low,
                      "volume": stmt.excluded.volume},
            )
            session.execute(stmt)
        session.commit()

        dates = [idx.date() if hasattr(idx, "date") else idx for idx in hist.index]
        return pd.DataFrame({"Date": dates, "Close": hist["Close"].values})


def _fetch_live(symbol: str, asset_class: AssetClass, period: str) -> pd.DataFrame:
    hist = fetch_historical_prices(symbol, asset_class, period=period)
    if hist is None or hist.empty:
        return pd.DataFrame(columns=["Date", "Close"])
    dates = [idx.date() if hasattr(idx, "date") else idx for idx in hist.index]
    return pd.DataFrame({"Date": dates, "Close": hist["Close"].values})


def _is_fresh(cached_rows: list[PriceHistory], period_start: date) -> bool:
    latest = max(c.date for c in cached_rows)
    earliest = min(c.date for c in cached_rows)
    is_recent = (date.today() - latest).days <= 3  # allow for weekends/holidays
    covers_range = earliest <= period_start + timedelta(days=5)
    return is_recent and covers_range
