"""Unit tests for src/db_portfolio.py.

A real SQLite-backed integration test isn't viable here: the shared Stock
model has a Postgres-only JSONB column that SQLite can't compile. Instead
these mock the SQLAlchemy session and assert on what gets queried/added —
thin-data-access-layer testing, not full ORM behavior.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.db.models import AssetClassEnum, TxnType
from src.db_portfolio import PortfolioWriteError, add_transaction, get_portfolio, load_portfolio_from_db


def _mock_session_factory(session: MagicMock):
    """Build a fake `get_sync_session_factory()` return value backing `with factory() as session:`."""
    factory = MagicMock()
    factory.return_value.__enter__.return_value = session
    factory.return_value.__exit__.return_value = False
    return factory


class TestAddTransaction:
    def test_new_holding_creates_stock_and_position(self, monkeypatch):
        session = MagicMock()
        session.query.return_value.filter_by.return_value.one_or_none.return_value = None
        monkeypatch.setattr("src.db_portfolio.get_sync_session_factory", lambda: _mock_session_factory(session))

        add_transaction(
            symbol="reliance",
            txn_type="buy",
            txn_date=date(2026, 1, 1),
            quantity=10,
            price=2500,
            charges=20,
            name="Reliance Industries",
            asset_class="equity_large_cap",
            sector="Energy",
        )

        added = [call.args[0] for call in session.add.call_args_list]
        assert len(added) == 3  # Stock, Position, Transaction
        stock, position, txn = added
        assert stock.symbol == "RELIANCE"  # uppercased
        assert stock.asset_class == AssetClassEnum.EQUITY_LARGE_CAP
        assert position.is_active is True
        assert txn.txn_type == TxnType.BUY
        assert txn.quantity == 10
        assert txn.amount == pytest.approx(10 * 2500 + 20)
        session.commit.assert_called_once()

    def test_new_holding_without_name_raises(self, monkeypatch):
        session = MagicMock()
        session.query.return_value.filter_by.return_value.one_or_none.return_value = None
        monkeypatch.setattr("src.db_portfolio.get_sync_session_factory", lambda: _mock_session_factory(session))

        with pytest.raises(PortfolioWriteError, match="new holding"):
            add_transaction(symbol="NEWCO", txn_type="buy", txn_date=date(2026, 1, 1), quantity=1, price=100)

    def test_invalid_transaction_type_raises(self, monkeypatch):
        session = MagicMock()
        monkeypatch.setattr("src.db_portfolio.get_sync_session_factory", lambda: _mock_session_factory(session))

        with pytest.raises(PortfolioWriteError, match="Invalid transaction type"):
            add_transaction(symbol="X", txn_type="yolo", txn_date=date(2026, 1, 1), quantity=1, price=100)

    def test_invalid_asset_class_raises(self, monkeypatch):
        session = MagicMock()
        session.query.return_value.filter_by.return_value.one_or_none.return_value = None
        monkeypatch.setattr("src.db_portfolio.get_sync_session_factory", lambda: _mock_session_factory(session))

        with pytest.raises(PortfolioWriteError, match="Invalid asset class"):
            add_transaction(
                symbol="X", txn_type="buy", txn_date=date(2026, 1, 1), quantity=1, price=100,
                name="X Corp", asset_class="not_a_real_class",
            )

    def test_existing_holding_only_adds_transaction(self, monkeypatch):
        existing_stock = MagicMock(id=1)
        existing_position = MagicMock(id=1, is_active=True)
        session = MagicMock()

        def query_side_effect(model):
            q = MagicMock()
            if model.__name__ == "Stock":
                q.filter_by.return_value.one_or_none.return_value = existing_stock
            else:
                q.filter_by.return_value.one_or_none.return_value = existing_position
            return q

        session.query.side_effect = query_side_effect
        monkeypatch.setattr("src.db_portfolio.get_sync_session_factory", lambda: _mock_session_factory(session))

        add_transaction(symbol="RELIANCE", txn_type="buy", txn_date=date(2026, 1, 1), quantity=5, price=2600)

        added = [call.args[0] for call in session.add.call_args_list]
        assert len(added) == 1  # only the Transaction — no new Stock/Position
        assert added[0].position_id == 1

    def test_reactivates_inactive_position(self, monkeypatch):
        existing_stock = MagicMock(id=1)
        existing_position = MagicMock(id=1, is_active=False)
        session = MagicMock()

        def query_side_effect(model):
            q = MagicMock()
            if model.__name__ == "Stock":
                q.filter_by.return_value.one_or_none.return_value = existing_stock
            else:
                q.filter_by.return_value.one_or_none.return_value = existing_position
            return q

        session.query.side_effect = query_side_effect
        monkeypatch.setattr("src.db_portfolio.get_sync_session_factory", lambda: _mock_session_factory(session))

        add_transaction(symbol="RELIANCE", txn_type="buy", txn_date=date(2026, 1, 1), quantity=5, price=2600)

        assert existing_position.is_active is True


class TestLoadPortfolioFromDb:
    def test_reconstructs_holdings_from_positions(self, monkeypatch):
        fake_txn = MagicMock(date=date(2026, 1, 1), txn_type=TxnType.BUY, quantity=10, price=100, charges=5)
        fake_stock = MagicMock(symbol="RELIANCE", name="Reliance Industries", sector="Energy")
        fake_stock.asset_class = AssetClassEnum.EQUITY_LARGE_CAP
        fake_position = MagicMock(current_price=150, notes=None)
        fake_position.stock = fake_stock
        fake_position.transactions = [fake_txn]

        session = MagicMock()
        session.query.return_value.filter_by.return_value.all.return_value = [fake_position]
        monkeypatch.setattr("src.db_portfolio.get_sync_session_factory", lambda: _mock_session_factory(session))

        portfolio = load_portfolio_from_db()

        assert len(portfolio.holdings) == 1
        holding = portfolio.holdings[0]
        assert holding.symbol == "RELIANCE"
        assert holding.current_price == 150
        assert len(holding.transactions) == 1
        assert holding.transactions[0].quantity == 10

    def test_empty_positions_returns_empty_portfolio(self, monkeypatch):
        session = MagicMock()
        session.query.return_value.filter_by.return_value.all.return_value = []
        monkeypatch.setattr("src.db_portfolio.get_sync_session_factory", lambda: _mock_session_factory(session))

        portfolio = load_portfolio_from_db()
        assert portfolio.holdings == []


class TestGetPortfolio:
    def test_falls_back_to_yaml_when_db_raises(self, monkeypatch):
        def boom():
            raise ConnectionError("no db")

        monkeypatch.setattr("src.db_portfolio.load_portfolio_from_db", boom)

        portfolio = get_portfolio()
        # Falls back to the real sample data/portfolio.yaml — just assert it didn't crash
        # and returned a Portfolio (possibly with holdings from the sample file).
        assert portfolio is not None

    def test_falls_back_to_yaml_when_db_is_empty(self, monkeypatch):
        from src.models import Portfolio

        monkeypatch.setattr("src.db_portfolio.load_portfolio_from_db", lambda: Portfolio(holdings=[]))

        portfolio = get_portfolio()
        assert portfolio is not None

    def test_uses_db_when_it_has_holdings(self, monkeypatch, make_holding):
        from src.models import Portfolio

        db_portfolio = Portfolio(holdings=[make_holding(symbol="DBHOLDING")])
        monkeypatch.setattr("src.db_portfolio.load_portfolio_from_db", lambda: db_portfolio)

        portfolio = get_portfolio()
        assert portfolio.holdings[0].symbol == "DBHOLDING"
