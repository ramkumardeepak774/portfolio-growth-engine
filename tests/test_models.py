"""Unit tests for src/models.py — dataclass properties."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.models import AssetClass, Goal, Holding, Portfolio, Transaction, TransactionType


class TestTransaction:
    def test_amount_includes_charges(self):
        t = Transaction(date=date.today(), type=TransactionType.BUY, quantity=10, price=100, charges=20)
        assert t.amount == 1020.0

    def test_amount_without_charges(self):
        t = Transaction(date=date.today(), type=TransactionType.BUY, quantity=10, price=100)
        assert t.amount == 1000.0


class TestHolding:
    def test_quantity_nets_buy_and_sell(self):
        h = Holding(
            symbol="X",
            name="X",
            asset_class=AssetClass.EQUITY_LARGE_CAP,
            transactions=[
                Transaction(date=date.today(), type=TransactionType.BUY, quantity=10, price=100),
                Transaction(date=date.today(), type=TransactionType.SELL, quantity=4, price=120),
            ],
        )
        assert h.quantity == 6

    def test_invested_amount_nets_buy_and_sell(self):
        h = Holding(
            symbol="X",
            name="X",
            asset_class=AssetClass.EQUITY_LARGE_CAP,
            transactions=[
                Transaction(date=date.today(), type=TransactionType.BUY, quantity=10, price=100),
                Transaction(date=date.today(), type=TransactionType.SELL, quantity=4, price=120),
            ],
        )
        # invested = 1000 (buy) - 480 (sell) = 520
        assert h.invested_amount == 520.0

    def test_current_value_with_no_price_is_zero(self):
        h = Holding(symbol="X", name="X", asset_class=AssetClass.CASH, current_price=None)
        assert h.current_value == 0.0

    def test_current_value(self):
        h = Holding(
            symbol="X",
            name="X",
            asset_class=AssetClass.EQUITY_LARGE_CAP,
            current_price=150,
            transactions=[Transaction(date=date.today(), type=TransactionType.BUY, quantity=10, price=100)],
        )
        assert h.current_value == 1500.0

    def test_pnl_and_pnl_percent(self):
        h = Holding(
            symbol="X",
            name="X",
            asset_class=AssetClass.EQUITY_LARGE_CAP,
            current_price=150,
            transactions=[Transaction(date=date.today(), type=TransactionType.BUY, quantity=10, price=100)],
        )
        assert h.pnl == 500.0
        assert h.pnl_percent == pytest.approx(50.0)

    def test_pnl_percent_zero_when_no_investment(self):
        h = Holding(symbol="X", name="X", asset_class=AssetClass.CASH)
        assert h.pnl_percent == 0.0

    def test_first_investment_date_ignores_sells(self):
        buy_date = date.today() - timedelta(days=500)
        sell_date = date.today() - timedelta(days=10)
        h = Holding(
            symbol="X",
            name="X",
            asset_class=AssetClass.EQUITY_LARGE_CAP,
            transactions=[
                Transaction(date=buy_date, type=TransactionType.BUY, quantity=10, price=100),
                Transaction(date=sell_date, type=TransactionType.SELL, quantity=4, price=120),
            ],
        )
        assert h.first_investment_date == buy_date

    def test_first_investment_date_none_when_no_buys(self):
        h = Holding(symbol="X", name="X", asset_class=AssetClass.CASH)
        assert h.first_investment_date is None


class TestPortfolio:
    def test_totals_sum_across_holdings(self, sample_portfolio):
        assert sample_portfolio.total_invested == pytest.approx(10000 + 5000)
        assert sample_portfolio.total_current_value == pytest.approx(15000 + 5500)

    def test_total_pnl(self, sample_portfolio):
        assert sample_portfolio.total_pnl == pytest.approx(20500 - 15000)

    def test_pnl_percent_zero_when_nothing_invested(self, empty_portfolio):
        assert empty_portfolio.total_pnl_percent == 0.0

    def test_holdings_by_asset_class_groups_correctly(self, sample_portfolio):
        grouped = sample_portfolio.holdings_by_asset_class()
        assert AssetClass.EQUITY_LARGE_CAP in grouped
        assert AssetClass.GOLD in grouped
        assert len(grouped[AssetClass.EQUITY_LARGE_CAP]) == 1

    def test_holdings_by_sector_defaults_to_unknown(self, make_holding):
        h = make_holding(sector=None)
        portfolio = Portfolio(holdings=[h])
        grouped = portfolio.holdings_by_sector()
        assert "Unknown" in grouped


class TestGoal:
    def test_target_corpus(self):
        g = Goal(name="G", target_multiplier=20, target_years=20, start_date=date.today(), initial_corpus=100000)
        assert g.target_corpus == 2_000_000

    def test_required_cagr(self):
        g = Goal(name="G", target_multiplier=20, target_years=20, start_date=date.today(), initial_corpus=100000)
        # 20x in 20 years ~ 16.2% CAGR
        assert g.required_cagr == pytest.approx(16.2, abs=0.1)

    def test_required_cagr_zero_when_no_years(self):
        g = Goal(name="G", target_multiplier=20, target_years=0, start_date=date.today(), initial_corpus=100000)
        assert g.required_cagr == 0.0

    def test_years_remaining_clamped_at_zero(self):
        g = Goal(
            name="G",
            target_multiplier=2,
            target_years=1,
            start_date=date.today() - timedelta(days=1000),
            initial_corpus=100000,
        )
        assert g.years_remaining == 0
