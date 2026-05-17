"""Portfolio Growth Engine — Data Models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class AssetClass(str, Enum):
    EQUITY_LARGE_CAP = "equity_large_cap"
    EQUITY_MID_CAP = "equity_mid_cap"
    EQUITY_SMALL_CAP = "equity_small_cap"
    EQUITY_MICRO_CAP = "equity_micro_cap"
    MUTUAL_FUND_EQUITY = "mf_equity"
    MUTUAL_FUND_HYBRID = "mf_hybrid"
    MUTUAL_FUND_DEBT = "mf_debt"
    MUTUAL_FUND_INDEX = "mf_index"
    MUTUAL_FUND_ELSS = "mf_elss"
    GOLD = "gold"
    FIXED_DEPOSIT = "fd"
    PPF = "ppf"
    EPF = "epf"
    NPS = "nps"
    REAL_ESTATE = "real_estate"
    CRYPTO = "crypto"
    CASH = "cash"
    OTHER = "other"


class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SIP = "sip"
    SWITCH = "switch"


@dataclass
class Transaction:
    date: date
    type: TransactionType
    quantity: float
    price: float  # per unit in INR
    charges: float = 0.0  # brokerage + taxes

    @property
    def amount(self) -> float:
        return self.quantity * self.price + self.charges


@dataclass
class Holding:
    symbol: str
    name: str
    asset_class: AssetClass
    transactions: list[Transaction] = field(default_factory=list)
    current_price: Optional[float] = None
    sector: Optional[str] = None
    notes: Optional[str] = None

    @property
    def quantity(self) -> float:
        total = 0.0
        for t in self.transactions:
            if t.type in (TransactionType.BUY, TransactionType.SIP):
                total += t.quantity
            elif t.type == TransactionType.SELL:
                total -= t.quantity
        return total

    @property
    def invested_amount(self) -> float:
        total = 0.0
        for t in self.transactions:
            if t.type in (TransactionType.BUY, TransactionType.SIP):
                total += t.amount
            elif t.type == TransactionType.SELL:
                total -= t.amount
        return total

    @property
    def current_value(self) -> float:
        if self.current_price is None:
            return 0.0
        return self.quantity * self.current_price

    @property
    def pnl(self) -> float:
        return self.current_value - self.invested_amount

    @property
    def pnl_percent(self) -> float:
        if self.invested_amount == 0:
            return 0.0
        return (self.pnl / self.invested_amount) * 100

    @property
    def first_investment_date(self) -> Optional[date]:
        buy_txns = [t for t in self.transactions if t.type in (TransactionType.BUY, TransactionType.SIP)]
        if not buy_txns:
            return None
        return min(t.date for t in buy_txns)


@dataclass
class Goal:
    name: str
    target_multiplier: float  # e.g. 1000 for 1000x
    target_years: int  # e.g. 20
    start_date: date
    initial_corpus: float  # starting amount in INR

    @property
    def target_corpus(self) -> float:
        return self.initial_corpus * self.target_multiplier

    @property
    def required_cagr(self) -> float:
        """CAGR needed to hit the target."""
        if self.target_years <= 0 or self.initial_corpus <= 0:
            return 0.0
        return (self.target_multiplier ** (1 / self.target_years) - 1) * 100

    @property
    def end_date(self) -> date:
        return date(self.start_date.year + self.target_years, self.start_date.month, self.start_date.day)

    @property
    def years_elapsed(self) -> float:
        today = date.today()
        delta = today - self.start_date
        return delta.days / 365.25

    @property
    def years_remaining(self) -> float:
        return max(0, self.target_years - self.years_elapsed)


@dataclass
class Portfolio:
    holdings: list[Holding] = field(default_factory=list)
    goals: list[Goal] = field(default_factory=list)

    @property
    def total_invested(self) -> float:
        return sum(h.invested_amount for h in self.holdings)

    @property
    def total_current_value(self) -> float:
        return sum(h.current_value for h in self.holdings)

    @property
    def total_pnl(self) -> float:
        return self.total_current_value - self.total_invested

    @property
    def total_pnl_percent(self) -> float:
        if self.total_invested == 0:
            return 0.0
        return (self.total_pnl / self.total_invested) * 100

    def holdings_by_asset_class(self) -> dict[AssetClass, list[Holding]]:
        result: dict[AssetClass, list[Holding]] = {}
        for h in self.holdings:
            result.setdefault(h.asset_class, []).append(h)
        return result

    def holdings_by_sector(self) -> dict[str, list[Holding]]:
        result: dict[str, list[Holding]] = {}
        for h in self.holdings:
            sector = h.sector or "Unknown"
            result.setdefault(sector, []).append(h)
        return result
