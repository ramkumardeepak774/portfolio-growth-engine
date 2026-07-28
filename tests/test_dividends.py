"""Unit tests for src/dividends.py — dividend income aggregation."""

from __future__ import annotations

from datetime import date

import pytest

from src.dividends import get_dividend_summary
from src.models import AssetClass, Holding, Portfolio, Transaction, TransactionType


def _dividend(d: date, qty: float, price: float) -> Transaction:
    return Transaction(date=d, type=TransactionType.DIVIDEND, quantity=qty, price=price)


def _buy(d: date, qty: float, price: float) -> Transaction:
    return Transaction(date=d, type=TransactionType.BUY, quantity=qty, price=price)


def _holding(symbol: str, name: str, transactions: list[Transaction]) -> Holding:
    return Holding(
        symbol=symbol,
        name=name,
        asset_class=AssetClass.EQUITY_LARGE_CAP,
        transactions=transactions,
        current_price=100.0,
    )


class TestGetDividendSummary:
    def test_empty_portfolio(self):
        summary = get_dividend_summary(Portfolio(holdings=[]), fy="2024-25")
        assert summary["total_dividend_income"] == 0
        assert summary["by_holding"] == []
        assert summary["by_month"] == []

    def test_single_dividend(self):
        holding = _holding("RELIANCE", "Reliance Industries", [_dividend(date(2024, 6, 1), 10, 5)])
        summary = get_dividend_summary(Portfolio(holdings=[holding]), fy="2024-25")
        assert summary["total_dividend_income"] == 50
        assert summary["by_holding"] == [{"symbol": "RELIANCE", "name": "Reliance Industries", "total": 50, "count": 1}]
        assert summary["by_month"] == [{"month": "2024-06", "total": 50}]

    def test_multiple_dividends_across_holdings(self):
        h1 = _holding("RELIANCE", "Reliance Industries", [_dividend(date(2024, 6, 1), 10, 5)])
        h2 = _holding("TCS", "Tata Consultancy", [_dividend(date(2024, 7, 1), 5, 20)])
        summary = get_dividend_summary(Portfolio(holdings=[h1, h2]), fy="2024-25")
        assert summary["total_dividend_income"] == 150  # 50 + 100

    def test_multiple_dividends_same_holding_aggregate(self):
        holding = _holding(
            "RELIANCE",
            "Reliance Industries",
            [_dividend(date(2024, 6, 1), 10, 5), _dividend(date(2024, 9, 1), 10, 6)],
        )
        summary = get_dividend_summary(Portfolio(holdings=[holding]), fy="2024-25")
        assert summary["by_holding"] == [{"symbol": "RELIANCE", "name": "Reliance Industries", "total": 110, "count": 2}]

    def test_fy_boundary_excludes_outside_range(self):
        holding = _holding(
            "RELIANCE",
            "Reliance Industries",
            [_dividend(date(2024, 3, 31), 10, 5), _dividend(date(2025, 4, 1), 10, 5)],  # just before and just after FY24-25
        )
        summary = get_dividend_summary(Portfolio(holdings=[holding]), fy="2024-25")
        assert summary["total_dividend_income"] == 0

    def test_fy_boundary_includes_edges(self):
        holding = _holding(
            "RELIANCE",
            "Reliance Industries",
            [_dividend(date(2024, 4, 1), 10, 5), _dividend(date(2025, 3, 31), 10, 5)],
        )
        summary = get_dividend_summary(Portfolio(holdings=[holding]), fy="2024-25")
        assert summary["total_dividend_income"] == 100

    def test_holding_with_no_dividends_not_in_breakdown(self):
        h1 = _holding("RELIANCE", "Reliance Industries", [_dividend(date(2024, 6, 1), 10, 5)])
        h2 = _holding("TCS", "Tata Consultancy", [_buy(date(2024, 1, 1), 5, 3000)])  # never pays a dividend
        summary = get_dividend_summary(Portfolio(holdings=[h1, h2]), fy="2024-25")
        symbols = [h["symbol"] for h in summary["by_holding"]]
        assert symbols == ["RELIANCE"]

    def test_non_dividend_transactions_ignored(self):
        holding = _holding(
            "RELIANCE",
            "Reliance Industries",
            [_buy(date(2024, 1, 1), 10, 2500), _dividend(date(2024, 6, 1), 10, 5)],
        )
        summary = get_dividend_summary(Portfolio(holdings=[holding]), fy="2024-25")
        assert summary["total_dividend_income"] == 50

    def test_monthly_aggregation_across_holdings(self):
        h1 = _holding("RELIANCE", "Reliance Industries", [_dividend(date(2024, 6, 15), 10, 5)])
        h2 = _holding("TCS", "Tata Consultancy", [_dividend(date(2024, 6, 20), 5, 10)])
        summary = get_dividend_summary(Portfolio(holdings=[h1, h2]), fy="2024-25")
        assert summary["by_month"] == [{"month": "2024-06", "total": 100}]  # 50 + 50

    def test_by_holding_sorted_by_total_descending(self):
        h1 = _holding("SMALL", "Small Div Co", [_dividend(date(2024, 6, 1), 1, 10)])
        h2 = _holding("BIG", "Big Div Co", [_dividend(date(2024, 6, 1), 100, 10)])
        summary = get_dividend_summary(Portfolio(holdings=[h1, h2]), fy="2024-25")
        assert [h["symbol"] for h in summary["by_holding"]] == ["BIG", "SMALL"]

    def test_fy_label_and_range_in_response(self):
        summary = get_dividend_summary(Portfolio(holdings=[]), fy="2024-25")
        assert summary["fy"] == "2024-25"
        assert summary["from"] == "2024-04-01"
        assert summary["to"] == "2025-03-31"
