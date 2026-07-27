"""Unit tests for src/tax_report.py — STCG/LTCG capital gains classification."""

from __future__ import annotations

from datetime import date

import pytest

from src.models import AssetClass, Holding, Portfolio, Transaction, TransactionType
from src.tax_report import InvalidFinancialYear, _parse_fy, generate_tax_report


def _buy(d: date, qty: float, price: float) -> Transaction:
    return Transaction(date=d, type=TransactionType.BUY, quantity=qty, price=price)


def _sell(d: date, qty: float, price: float) -> Transaction:
    return Transaction(date=d, type=TransactionType.SELL, quantity=qty, price=price)


def _equity_holding(symbol: str, transactions: list[Transaction]) -> Holding:
    return Holding(
        symbol=symbol,
        name=symbol,
        asset_class=AssetClass.EQUITY_LARGE_CAP,
        transactions=transactions,
        current_price=100.0,
    )


class TestParseFy:
    def test_parses_explicit_fy(self):
        start_year, start, end = _parse_fy("2024-25")
        assert start_year == 2024
        assert start == date(2024, 4, 1)
        assert end == date(2025, 3, 31)

    def test_rejects_malformed_fy(self):
        with pytest.raises(InvalidFinancialYear):
            _parse_fy("not-a-fy")

    def test_defaults_to_current_fy(self, monkeypatch):
        class FakeDate(date):
            @classmethod
            def today(cls):
                return date(2025, 6, 15)  # June -> FY2025-26

        monkeypatch.setattr("src.tax_report.date", FakeDate)
        start_year, start, end = _parse_fy(None)
        assert start_year == 2025
        assert start == date(2025, 4, 1)

    def test_defaults_to_previous_fy_before_april(self, monkeypatch):
        class FakeDate(date):
            @classmethod
            def today(cls):
                return date(2025, 2, 1)  # Feb -> FY2024-25

        monkeypatch.setattr("src.tax_report.date", FakeDate)
        start_year, start, end = _parse_fy(None)
        assert start_year == 2024


class TestGenerateTaxReport:
    def test_empty_portfolio(self):
        report = generate_tax_report(Portfolio(holdings=[]), fy="2024-25")
        assert report["stcg"]["total_gain"] == 0
        assert report["ltcg"]["total_gain"] == 0
        assert report["stcg"]["lots"] == []
        assert report["unsupported_asset_classes"] == []

    def test_short_term_gain_classified_correctly(self):
        """Bought and sold 6 months apart -> STCG."""
        holding = _equity_holding(
            "TEST",
            [_buy(date(2024, 4, 10), 10, 100), _sell(date(2024, 10, 10), 10, 150)],
        )
        report = generate_tax_report(Portfolio(holdings=[holding]), fy="2024-25")
        assert report["ltcg"]["total_gain"] == 0
        assert report["stcg"]["total_gain"] == pytest.approx(500)  # 10 * (150-100)
        assert len(report["stcg"]["lots"]) == 1

    def test_long_term_gain_at_exactly_12_months(self):
        """Bought 2023-04-10, sold 2024-04-10 -> exactly 12 calendar months -> LTCG."""
        holding = _equity_holding(
            "TEST",
            [_buy(date(2023, 4, 10), 10, 100), _sell(date(2024, 4, 10), 10, 150)],
        )
        report = generate_tax_report(Portfolio(holdings=[holding]), fy="2024-25")
        assert report["stcg"]["total_gain"] == 0
        assert report["ltcg"]["total_gain"] == pytest.approx(500)

    def test_just_under_12_months_is_short_term(self):
        holding = _equity_holding(
            "TEST",
            [_buy(date(2023, 4, 10), 10, 100), _sell(date(2024, 4, 9), 10, 150)],
        )
        report = generate_tax_report(Portfolio(holdings=[holding]), fy="2024-25")
        assert report["stcg"]["total_gain"] == pytest.approx(500)
        assert report["ltcg"]["total_gain"] == 0

    def test_leap_year_february_does_not_shift_the_threshold(self):
        """A 12-calendar-month hold spanning a leap Feb (2024) should still
        read as exactly 12 months, not accidentally short by a day count."""
        holding = _equity_holding(
            "TEST",
            [_buy(date(2023, 2, 15), 10, 100), _sell(date(2024, 2, 15), 10, 150)],
        )
        report = generate_tax_report(Portfolio(holdings=[holding]), fy="2023-24")
        assert report["ltcg"]["total_gain"] == pytest.approx(500)
        assert report["stcg"]["total_gain"] == 0

    def test_fifo_matches_earliest_lot_first(self):
        """Two buys, one partial sell -> should consume the earlier (2023) lot first."""
        holding = _equity_holding(
            "TEST",
            [
                _buy(date(2023, 1, 1), 10, 100),
                _buy(date(2024, 6, 1), 10, 200),
                _sell(date(2024, 7, 1), 10, 250),
            ],
        )
        report = generate_tax_report(Portfolio(holdings=[holding]), fy="2024-25")
        # Matched against the 2023 lot (>=12mo held) -> LTCG, gain = 10*(250-100)
        assert report["ltcg"]["total_gain"] == pytest.approx(1500)
        assert report["stcg"]["total_gain"] == 0
        assert report["ltcg"]["lots"][0]["buy_date"] == "2023-01-01"

    def test_partial_sell_splits_across_two_lots(self):
        holding = _equity_holding(
            "TEST",
            [
                _buy(date(2023, 1, 1), 5, 100),
                _buy(date(2023, 6, 1), 5, 120),
                _sell(date(2024, 6, 1), 8, 200),
            ],
        )
        report = generate_tax_report(Portfolio(holdings=[holding]), fy="2024-25")
        assert len(report["ltcg"]["lots"]) == 2
        # 5 @ 100 (full first lot) + 3 @ 120 (partial second lot)
        expected = 5 * (200 - 100) + 3 * (200 - 120)
        assert report["ltcg"]["total_gain"] == pytest.approx(expected)

    def test_sell_outside_fy_is_excluded(self):
        holding = _equity_holding(
            "TEST",
            [_buy(date(2022, 1, 1), 10, 100), _sell(date(2023, 1, 1), 10, 150)],
        )
        report = generate_tax_report(Portfolio(holdings=[holding]), fy="2024-25")
        assert report["stcg"]["total_gain"] == 0
        assert report["ltcg"]["total_gain"] == 0

    def test_sell_at_fy_boundary_included(self):
        """March 31 is the last day of the Indian FY."""
        holding = _equity_holding(
            "TEST",
            [_buy(date(2023, 1, 1), 10, 100), _sell(date(2025, 3, 31), 10, 150)],
        )
        report = generate_tax_report(Portfolio(holdings=[holding]), fy="2024-25")
        assert report["ltcg"]["total_gain"] == pytest.approx(500)

    def test_non_equity_asset_class_flagged_as_unsupported(self):
        gold_holding = Holding(
            symbol="GOLDBEES",
            name="Gold ETF",
            asset_class=AssetClass.GOLD,
            transactions=[_buy(date(2023, 1, 1), 10, 100), _sell(date(2024, 6, 1), 10, 150)],
            current_price=150,
        )
        report = generate_tax_report(Portfolio(holdings=[gold_holding]), fy="2024-25")
        assert report["stcg"]["total_gain"] == 0
        assert report["ltcg"]["total_gain"] == 0
        assert len(report["unsupported_asset_classes"]) == 1
        assert report["unsupported_asset_classes"][0]["asset_class"] == "gold"
        assert "GOLDBEES" in report["unsupported_asset_classes"][0]["symbols"]

    def test_non_equity_holding_with_no_transactions_not_flagged(self):
        """A holding that's never been traded shouldn't clutter the unsupported list."""
        gold_holding = Holding(
            symbol="GOLDBEES", name="Gold ETF", asset_class=AssetClass.GOLD, transactions=[],
        )
        report = generate_tax_report(Portfolio(holdings=[gold_holding]), fy="2024-25")
        assert report["unsupported_asset_classes"] == []

    def test_dividend_and_switch_do_not_affect_lots(self):
        holding = _equity_holding(
            "TEST",
            [
                _buy(date(2023, 1, 1), 10, 100),
                Transaction(date=date(2023, 6, 1), type=TransactionType.DIVIDEND, quantity=10, price=2),
                _sell(date(2024, 6, 1), 10, 150),
            ],
        )
        report = generate_tax_report(Portfolio(holdings=[holding]), fy="2024-25")
        assert report["ltcg"]["total_gain"] == pytest.approx(500)

    def test_oversold_position_does_not_crash(self):
        """Selling more than was ever bought (bad data upstream) should be
        handled gracefully, not raise — the matchable portion still reports."""
        holding = _equity_holding(
            "TEST",
            [_buy(date(2023, 1, 1), 5, 100), _sell(date(2024, 6, 1), 10, 150)],
        )
        report = generate_tax_report(Portfolio(holdings=[holding]), fy="2024-25")
        assert report["ltcg"]["total_gain"] == pytest.approx(5 * (150 - 100))

    def test_loss_is_negative_gain(self):
        holding = _equity_holding(
            "TEST",
            [_buy(date(2024, 4, 1), 10, 200), _sell(date(2024, 6, 1), 10, 150)],
        )
        report = generate_tax_report(Portfolio(holdings=[holding]), fy="2024-25")
        assert report["stcg"]["total_gain"] == pytest.approx(-500)

    def test_fy_label_in_response(self):
        report = generate_tax_report(Portfolio(holdings=[]), fy="2024-25")
        assert report["fy"] == "2024-25"
        assert report["from"] == "2024-04-01"
        assert report["to"] == "2025-03-31"
