"""Unit tests for src/db_watchlist.py.

Mocks the SQLAlchemy session (same reasoning as test_db_portfolio.py — the
shared Stock model has a Postgres-only JSONB column SQLite can't compile).
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.db.models import AssetClassEnum
from src.db_portfolio import PortfolioWriteError
from src.db_watchlist import (
    WatchlistItemNotFoundError,
    add_to_watchlist,
    get_watchlist,
    remove_from_watchlist,
)


def _mock_session_factory(session: MagicMock):
    factory = MagicMock()
    factory.return_value.__enter__.return_value = session
    factory.return_value.__exit__.return_value = False
    return factory


def _query_dispatch(session: MagicMock, *, stock=None, item=None):
    def query_side_effect(model):
        q = MagicMock()
        if model.__name__ == "Stock":
            q.filter_by.return_value.one_or_none.return_value = stock
        else:
            q.filter_by.return_value.one_or_none.return_value = item
        return q

    session.query.side_effect = query_side_effect


class TestAddToWatchlist:
    def test_new_symbol_creates_stock_and_item(self, monkeypatch):
        session = MagicMock()
        _query_dispatch(session, stock=None, item=None)
        monkeypatch.setattr("src.db_watchlist.get_sync_session_factory", lambda: _mock_session_factory(session))

        add_to_watchlist(
            "reliance", name="Reliance Industries", asset_class="equity_large_cap", target_price=3000,
        )

        added = [call.args[0] for call in session.add.call_args_list]
        assert len(added) == 2  # Stock, WatchlistItem
        stock, item = added
        assert stock.symbol == "RELIANCE"
        assert stock.asset_class == AssetClassEnum.EQUITY_LARGE_CAP
        assert item.target_price == 3000
        session.commit.assert_called_once()

    def test_new_symbol_without_name_raises(self, monkeypatch):
        session = MagicMock()
        _query_dispatch(session, stock=None, item=None)
        monkeypatch.setattr("src.db_watchlist.get_sync_session_factory", lambda: _mock_session_factory(session))

        with pytest.raises(PortfolioWriteError, match="new symbol"):
            add_to_watchlist("NEWCO")

    def test_invalid_asset_class_raises(self, monkeypatch):
        session = MagicMock()
        _query_dispatch(session, stock=None, item=None)
        monkeypatch.setattr("src.db_watchlist.get_sync_session_factory", lambda: _mock_session_factory(session))

        with pytest.raises(PortfolioWriteError, match="Invalid asset class"):
            add_to_watchlist("X", name="X Corp", asset_class="not_a_real_class")

    def test_existing_stock_new_watchlist_item(self, monkeypatch):
        existing_stock = MagicMock(id=1)
        session = MagicMock()
        _query_dispatch(session, stock=existing_stock, item=None)
        monkeypatch.setattr("src.db_watchlist.get_sync_session_factory", lambda: _mock_session_factory(session))

        add_to_watchlist("RELIANCE", target_price=3000)

        added = [call.args[0] for call in session.add.call_args_list]
        assert len(added) == 1  # only the WatchlistItem — stock already existed
        assert added[0].stock_id == 1

    def test_already_on_watchlist_updates_instead_of_erroring(self, monkeypatch):
        existing_stock = MagicMock(id=1)
        existing_item = MagicMock(target_price=100, notes="old note")
        session = MagicMock()
        _query_dispatch(session, stock=existing_stock, item=existing_item)
        monkeypatch.setattr("src.db_watchlist.get_sync_session_factory", lambda: _mock_session_factory(session))

        add_to_watchlist("RELIANCE", target_price=200)

        session.add.assert_not_called()  # no new row — updated in place
        assert existing_item.target_price == 200
        assert existing_item.notes == "old note"  # not provided, left alone
        session.commit.assert_called_once()


class TestRemoveFromWatchlist:
    def test_removes_and_commits(self, monkeypatch):
        existing_stock = MagicMock(id=1)
        existing_item = MagicMock()
        session = MagicMock()
        _query_dispatch(session, stock=existing_stock, item=existing_item)
        monkeypatch.setattr("src.db_watchlist.get_sync_session_factory", lambda: _mock_session_factory(session))

        remove_from_watchlist("RELIANCE")

        session.delete.assert_called_once_with(existing_item)
        session.commit.assert_called_once()

    def test_not_found_when_no_stock(self, monkeypatch):
        session = MagicMock()
        _query_dispatch(session, stock=None, item=None)
        monkeypatch.setattr("src.db_watchlist.get_sync_session_factory", lambda: _mock_session_factory(session))

        with pytest.raises(WatchlistItemNotFoundError):
            remove_from_watchlist("NOTREAL")

    def test_not_found_when_stock_exists_but_not_watchlisted(self, monkeypatch):
        existing_stock = MagicMock(id=1)
        session = MagicMock()
        _query_dispatch(session, stock=existing_stock, item=None)
        monkeypatch.setattr("src.db_watchlist.get_sync_session_factory", lambda: _mock_session_factory(session))

        with pytest.raises(WatchlistItemNotFoundError):
            remove_from_watchlist("RELIANCE")


class TestGetWatchlist:
    def test_empty(self, monkeypatch):
        session = MagicMock()
        session.query.return_value.order_by.return_value.all.return_value = []
        monkeypatch.setattr("src.db_watchlist.get_sync_session_factory", lambda: _mock_session_factory(session))

        assert get_watchlist() == []

    def test_populated(self, monkeypatch):
        fake_stock = MagicMock(symbol="RELIANCE", sector="Energy")
        fake_stock.name = "Reliance Industries"  # `name=` in the constructor sets the mock's repr, not this attribute
        fake_stock.asset_class = AssetClassEnum.EQUITY_LARGE_CAP
        added_at = datetime(2026, 1, 1)
        fake_item = MagicMock(target_price=3000, notes="watching", added_at=added_at)
        fake_item.stock = fake_stock

        session = MagicMock()
        session.query.return_value.order_by.return_value.all.return_value = [fake_item]
        monkeypatch.setattr("src.db_watchlist.get_sync_session_factory", lambda: _mock_session_factory(session))

        result = get_watchlist()
        assert len(result) == 1
        assert result[0] == {
            "symbol": "RELIANCE",
            "name": "Reliance Industries",
            "asset_class": "equity_large_cap",
            "sector": "Energy",
            "target_price": 3000,
            "notes": "watching",
            "added_at": added_at,
        }
