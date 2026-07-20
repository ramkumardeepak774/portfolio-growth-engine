"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.models import AssetClass, Goal, Holding, Portfolio, Transaction, TransactionType


@pytest.fixture
def today() -> date:
    return date.today()


@pytest.fixture
def make_holding():
    """Factory for building a Holding with a single BUY transaction N years ago."""

    def _make(
        symbol: str = "RELIANCE",
        asset_class: AssetClass = AssetClass.EQUITY_LARGE_CAP,
        buy_price: float = 100.0,
        quantity: float = 10.0,
        current_price: float = 150.0,
        years_ago: float = 2.0,
        sector: str | None = "Energy",
    ) -> Holding:
        buy_date = date.today() - timedelta(days=int(years_ago * 365.25))
        return Holding(
            symbol=symbol,
            name=symbol.title(),
            asset_class=asset_class,
            current_price=current_price,
            sector=sector,
            transactions=[
                Transaction(date=buy_date, type=TransactionType.BUY, quantity=quantity, price=buy_price),
            ],
        )

    return _make


@pytest.fixture
def sample_portfolio(make_holding) -> Portfolio:
    """A small two-holding portfolio for allocation/concentration tests."""
    return Portfolio(
        holdings=[
            make_holding(
                symbol="RELIANCE",
                asset_class=AssetClass.EQUITY_LARGE_CAP,
                buy_price=100.0,
                quantity=100.0,
                current_price=150.0,
                years_ago=3.0,
                sector="Energy",
            ),
            make_holding(
                symbol="GOLDBEES",
                asset_class=AssetClass.GOLD,
                buy_price=50.0,
                quantity=100.0,
                current_price=55.0,
                years_ago=1.0,
                sector="Commodities",
            ),
        ],
        goals=[
            Goal(
                name="Retirement",
                target_multiplier=20,
                target_years=20,
                start_date=date.today() - timedelta(days=365),
                initial_corpus=100000.0,
            ),
        ],
    )


@pytest.fixture
def empty_portfolio() -> Portfolio:
    return Portfolio(holdings=[], goals=[])
