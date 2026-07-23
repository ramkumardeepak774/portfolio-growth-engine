"""Unit tests for src/analyzer.py — the core financial calculations."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.analyzer import (
    asset_class_allocation,
    calculate_cagr,
    calculate_portfolio_cagr,
    calculate_portfolio_xirr,
    calculate_xirr,
    concentration_risk,
    holding_performance_table,
    sector_allocation,
)
from src.models import AssetClass, Transaction, TransactionType


class TestCalculateCagr:
    def test_doubles_in_one_year(self):
        assert calculate_cagr(100, 200, 1) == pytest.approx(100.0)

    def test_flat_growth_is_zero(self):
        assert calculate_cagr(100, 100, 5) == pytest.approx(0.0)

    def test_ten_percent_over_ten_years(self):
        # 100 -> 259.37 @ 10% CAGR over 10 years
        final = 100 * (1.10 ** 10)
        assert calculate_cagr(100, final, 10) == pytest.approx(10.0, abs=1e-6)

    def test_zero_initial_returns_zero(self):
        assert calculate_cagr(0, 200, 5) == 0.0

    def test_negative_initial_returns_zero(self):
        assert calculate_cagr(-100, 200, 5) == 0.0

    def test_zero_years_returns_zero(self):
        assert calculate_cagr(100, 200, 0) == 0.0

    def test_negative_years_returns_zero(self):
        assert calculate_cagr(100, 200, -1) == 0.0

    def test_loss(self):
        assert calculate_cagr(200, 100, 1) == pytest.approx(-50.0)

    def test_large_return_over_near_zero_years_returns_zero_not_overflow(self):
        """Regression test: a CSV-imported holding bought "today" has
        years_held ~= 1/365.25 by the next day. Annualizing a large real
        return (e.g. VAML's ~9.3x) over that short a period overflows a
        float when raised to the ~365th power — production 500'd on this."""
        result = calculate_cagr(11605, 107800, 1 / 365.25)
        assert result == 0.0


class TestCalculateXirr:
    def test_single_buy_with_gain_is_positive(self, make_holding):
        holding = make_holding(buy_price=100, quantity=10, current_price=150, years_ago=2)
        result = calculate_xirr(holding)
        assert result is not None
        assert result > 0

    def test_single_buy_with_loss_is_negative(self, make_holding):
        holding = make_holding(buy_price=200, quantity=10, current_price=100, years_ago=2)
        result = calculate_xirr(holding)
        assert result is not None
        assert result < 0

    def test_no_transactions_and_no_value_returns_none(self):
        from src.models import Holding

        holding = Holding(symbol="EMPTY", name="Empty", asset_class=AssetClass.CASH)
        assert calculate_xirr(holding) is None

    def test_single_transaction_no_current_value_returns_none(self):
        from src.models import Holding

        holding = Holding(
            symbol="X",
            name="X",
            asset_class=AssetClass.EQUITY_LARGE_CAP,
            current_price=None,
            transactions=[
                Transaction(date=date.today() - timedelta(days=100), type=TransactionType.BUY, quantity=10, price=100)
            ],
        )
        # current_value is 0 (no current_price) -> only one cashflow -> None
        assert calculate_xirr(holding) is None

    def test_dividend_counted_as_inflow(self, make_holding):
        holding = make_holding(buy_price=100, quantity=10, current_price=110, years_ago=1)
        holding.transactions.append(
            Transaction(date=date.today() - timedelta(days=180), type=TransactionType.DIVIDEND, quantity=10, price=2)
        )
        result = calculate_xirr(holding)
        assert result is not None

    def test_same_day_buy_and_valuation_returns_none_not_inf(self, make_holding):
        """Regression test: XIRR is undefined with zero elapsed time between
        cashflows (e.g. a CSV-imported holding bought "today" with current
        value also dated today). pyxirr returns inf rather than raising —
        that broke JSON serialization in production before this was guarded."""
        holding = make_holding(buy_price=100, quantity=10, current_price=150, years_ago=0)
        result = calculate_xirr(holding)
        assert result is None


class TestPortfolioCagrAndXirr:
    def test_portfolio_cagr_uses_earliest_holding_date(self, sample_portfolio):
        cagr = calculate_portfolio_cagr(sample_portfolio)
        earliest = min(h.first_investment_date for h in sample_portfolio.holdings)
        years = (date.today() - earliest).days / 365.25
        expected = calculate_cagr(
            sample_portfolio.total_invested, sample_portfolio.total_current_value, years
        )
        assert cagr == pytest.approx(expected)

    def test_portfolio_cagr_empty_portfolio_is_zero(self, empty_portfolio):
        assert calculate_portfolio_cagr(empty_portfolio) == 0.0

    def test_portfolio_xirr_returns_value_for_populated_portfolio(self, sample_portfolio):
        assert calculate_portfolio_xirr(sample_portfolio) is not None

    def test_portfolio_xirr_none_for_empty_portfolio(self, empty_portfolio):
        assert calculate_portfolio_xirr(empty_portfolio) is None

    def test_portfolio_xirr_same_day_only_returns_none_not_inf(self, make_holding):
        from src.models import Portfolio

        portfolio = Portfolio(holdings=[make_holding(buy_price=100, quantity=10, current_price=150, years_ago=0)])
        assert calculate_portfolio_xirr(portfolio) is None


class TestAssetClassAllocation:
    def test_splits_by_asset_class(self, sample_portfolio):
        alloc = asset_class_allocation(sample_portfolio)
        assert set(alloc.keys()) == {AssetClass.EQUITY_LARGE_CAP.value, AssetClass.GOLD.value}
        assert alloc[AssetClass.EQUITY_LARGE_CAP.value]["value"] == pytest.approx(15000.0)
        assert alloc[AssetClass.GOLD.value]["value"] == pytest.approx(5500.0)

    def test_percentages_sum_to_100(self, sample_portfolio):
        alloc = asset_class_allocation(sample_portfolio)
        total_pct = sum(v["percent"] for v in alloc.values())
        assert total_pct == pytest.approx(100.0, abs=0.1)

    def test_empty_portfolio_returns_empty_dict(self, empty_portfolio):
        assert asset_class_allocation(empty_portfolio) == {}


class TestSectorAllocation:
    def test_splits_by_sector(self, sample_portfolio):
        alloc = sector_allocation(sample_portfolio)
        assert set(alloc.keys()) == {"Energy", "Commodities"}

    def test_unknown_sector_bucketed(self, make_holding):
        from src.models import Portfolio

        holding = make_holding(sector=None)
        portfolio = Portfolio(holdings=[holding])
        alloc = sector_allocation(portfolio)
        assert "Unknown" in alloc


class TestConcentrationRisk:
    def test_top_holdings_sorted_by_value_desc(self, sample_portfolio):
        result = concentration_risk(sample_portfolio, top_n=1)
        assert len(result["top_holdings"]) == 1
        assert result["top_holdings"][0]["symbol"] == "RELIANCE"

    def test_top_percent_matches_manual_calc(self, sample_portfolio):
        result = concentration_risk(sample_portfolio, top_n=1)
        assert result["top_percent"] == pytest.approx(15000 / 20500 * 100, abs=0.01)

    def test_empty_portfolio(self, empty_portfolio):
        result = concentration_risk(empty_portfolio)
        assert result == {"top_holdings": [], "top_percent": 0}


class TestHoldingPerformanceTable:
    def test_returns_dataframe_with_expected_columns(self, sample_portfolio):
        df = holding_performance_table(sample_portfolio)
        assert len(df) == 2
        assert "Symbol" in df.columns
        assert "XIRR %" in df.columns

    def test_sorted_by_current_value_desc(self, sample_portfolio):
        df = holding_performance_table(sample_portfolio)
        assert df.iloc[0]["Symbol"] == "RELIANCE"

    def test_empty_portfolio_returns_empty_dataframe(self, empty_portfolio):
        df = holding_performance_table(empty_portfolio)
        assert df.empty
