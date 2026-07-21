"""Unit tests for analyzer.portfolio_value_series — real weighted portfolio
value reconstruction, mocking out the price source so nothing hits the
network or a real database.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from src.analyzer import portfolio_value_series
from src.models import AssetClass, Holding, Portfolio, Transaction, TransactionType


def _equity_holding(symbol: str, quantity: float, buy_date: date, asset_class=AssetClass.EQUITY_LARGE_CAP) -> Holding:
    return Holding(
        symbol=symbol,
        name=symbol,
        asset_class=asset_class,
        current_price=100,
        transactions=[Transaction(date=buy_date, type=TransactionType.BUY, quantity=quantity, price=100)],
    )


def _price_df(prices: dict[str, float]) -> pd.DataFrame:
    """Build a Date/Close DataFrame from {iso_date: close}."""
    return pd.DataFrame({"Date": list(prices.keys()), "Close": list(prices.values())})


class TestPortfolioValueSeries:
    def test_single_holding_weighted_by_quantity(self, monkeypatch):
        d0, d1, d2 = "2026-01-01", "2026-01-02", "2026-01-03"
        holding = _equity_holding("RELIANCE", quantity=10, buy_date=date(2025, 1, 1))
        portfolio = Portfolio(holdings=[holding])

        def fake_get_price_history(symbol, asset_class, period="1y"):
            assert symbol == "RELIANCE"
            return _price_df({d0: 100.0, d1: 110.0, d2: 120.0})

        monkeypatch.setattr("src.price_cache.get_price_history", fake_get_price_history)

        series = portfolio_value_series(portfolio, period="1y")
        by_date = {row["date"]: row["value"] for row in series}
        assert by_date[d0] == pytest.approx(1000.0)
        assert by_date[d1] == pytest.approx(1100.0)
        assert by_date[d2] == pytest.approx(1200.0)

    def test_sums_across_multiple_holdings(self, monkeypatch):
        d0 = "2026-01-01"
        h1 = _equity_holding("A", quantity=10, buy_date=date(2025, 1, 1))
        h2 = _equity_holding("B", quantity=5, buy_date=date(2025, 1, 1), asset_class=AssetClass.EQUITY_MID_CAP)
        portfolio = Portfolio(holdings=[h1, h2])

        def fake_get_price_history(symbol, asset_class, period="1y"):
            price = {"A": 100.0, "B": 200.0}[symbol]
            return _price_df({d0: price})

        monkeypatch.setattr("src.price_cache.get_price_history", fake_get_price_history)

        series = portfolio_value_series(portfolio, period="1y")
        assert len(series) == 1
        # A: 10 * 100 = 1000, B: 5 * 200 = 1000 -> total 2000
        assert series[0]["value"] == pytest.approx(2000.0)

    def test_quantity_reflects_transactions_before_each_date(self, monkeypatch, make_holding):
        """Buying more mid-series should increase value from that date forward, not before."""
        from src.models import Holding, Transaction, TransactionType

        d0, d1, d2 = "2026-01-01", "2026-01-02", "2026-01-03"
        holding = Holding(
            symbol="X",
            name="X",
            asset_class=AssetClass.EQUITY_LARGE_CAP,
            current_price=100,
            transactions=[
                Transaction(date=date(2026, 1, 1), type=TransactionType.BUY, quantity=10, price=100),
                Transaction(date=date(2026, 1, 2), type=TransactionType.BUY, quantity=5, price=100),
            ],
        )
        portfolio = Portfolio(holdings=[holding])

        def fake_get_price_history(symbol, asset_class, period="1y"):
            return _price_df({d0: 100.0, d1: 100.0, d2: 100.0})

        monkeypatch.setattr("src.price_cache.get_price_history", fake_get_price_history)

        series = portfolio_value_series(portfolio, period="1y")
        by_date = {row["date"]: row["value"] for row in series}
        assert by_date[d0] == pytest.approx(1000.0)  # 10 units
        assert by_date[d1] == pytest.approx(1500.0)  # 15 units after the second buy
        assert by_date[d2] == pytest.approx(1500.0)

    def test_non_priceable_asset_classes_excluded(self, monkeypatch, make_holding):
        holding = make_holding(symbol="GOLDBEES", asset_class=AssetClass.GOLD, quantity=10, years_ago=0.1)
        portfolio = Portfolio(holdings=[holding])

        def fake_get_price_history(symbol, asset_class, period="1y"):
            pytest.fail("get_price_history should not be called for non-priceable asset classes")

        monkeypatch.setattr("src.price_cache.get_price_history", fake_get_price_history)

        assert portfolio_value_series(portfolio, period="1y") == []

    def test_empty_portfolio_returns_empty_list(self, empty_portfolio):
        assert portfolio_value_series(empty_portfolio, period="1y") == []

    def test_holding_with_no_price_data_is_skipped(self, monkeypatch, make_holding):
        holding = make_holding(symbol="DELISTED", asset_class=AssetClass.EQUITY_SMALL_CAP, quantity=10, years_ago=0.1)
        portfolio = Portfolio(holdings=[holding])

        def fake_get_price_history(symbol, asset_class, period="1y"):
            return pd.DataFrame(columns=["Date", "Close"])

        monkeypatch.setattr("src.price_cache.get_price_history", fake_get_price_history)

        assert portfolio_value_series(portfolio, period="1y") == []
