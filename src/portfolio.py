"""Load portfolio data from YAML config files."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from .models import (
    AssetClass,
    Goal,
    Holding,
    Portfolio,
    Transaction,
    TransactionType,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _parse_date(val: Any) -> date:
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    return datetime.strptime(str(val), "%Y-%m-%d").date()


def _parse_transaction(raw: dict) -> Transaction:
    return Transaction(
        date=_parse_date(raw["date"]),
        type=TransactionType(raw["type"]),
        quantity=float(raw["quantity"]),
        price=float(raw["price"]),
        charges=float(raw.get("charges", 0)),
    )


def _parse_holding(raw: dict) -> Holding:
    transactions = [_parse_transaction(t) for t in raw.get("transactions", [])]
    current_price = raw.get("current_price")
    if current_price is not None:
        current_price = float(current_price)
    return Holding(
        symbol=raw["symbol"],
        name=raw["name"],
        asset_class=AssetClass(raw["asset_class"]),
        transactions=transactions,
        current_price=current_price,
        sector=raw.get("sector"),
        notes=raw.get("notes"),
    )


def _parse_goal(raw: dict) -> Goal:
    return Goal(
        name=raw["name"],
        target_multiplier=float(raw["target_multiplier"]),
        target_years=int(raw["target_years"]),
        start_date=_parse_date(raw["start_date"]),
        initial_corpus=float(raw["initial_corpus"]),
    )


def load_portfolio(portfolio_path: Path | None = None, goals_path: Path | None = None) -> Portfolio:
    """Load portfolio from YAML files."""
    portfolio_path = portfolio_path or DATA_DIR / "portfolio.yaml"
    goals_path = goals_path or DATA_DIR / "goals.yaml"

    holdings: list[Holding] = []
    goals: list[Goal] = []

    if portfolio_path.exists():
        with open(portfolio_path) as f:
            data = yaml.safe_load(f) or {}
        for raw in data.get("holdings", []):
            holdings.append(_parse_holding(raw))

    if goals_path.exists():
        with open(goals_path) as f:
            data = yaml.safe_load(f) or {}
        for raw in data.get("goals", []):
            goals.append(_parse_goal(raw))

    return Portfolio(holdings=holdings, goals=goals)


def save_portfolio(portfolio: Portfolio, portfolio_path: Path | None = None) -> None:
    """Save portfolio holdings back to YAML."""
    portfolio_path = portfolio_path or DATA_DIR / "portfolio.yaml"

    data = {"holdings": []}
    for h in portfolio.holdings:
        holding_dict = {
            "symbol": h.symbol,
            "name": h.name,
            "asset_class": h.asset_class.value,
            "sector": h.sector,
            "notes": h.notes,
            "transactions": [
                {
                    "date": t.date.isoformat(),
                    "type": t.type.value,
                    "quantity": t.quantity,
                    "price": t.price,
                    "charges": t.charges,
                }
                for t in h.transactions
            ],
        }
        data["holdings"].append(holding_dict)

    portfolio_path.parent.mkdir(parents=True, exist_ok=True)
    with open(portfolio_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
