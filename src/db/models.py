"""SQLAlchemy ORM models for all 4 layers."""

from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .engine import Base


# =====================================================================
# ENUMS
# =====================================================================

class AssetClassEnum(str, enum.Enum):
    EQUITY_LARGE_CAP = "equity_large_cap"
    EQUITY_MID_CAP = "equity_mid_cap"
    EQUITY_SMALL_CAP = "equity_small_cap"
    EQUITY_MICRO_CAP = "equity_micro_cap"
    MF_EQUITY = "mf_equity"
    MF_HYBRID = "mf_hybrid"
    MF_DEBT = "mf_debt"
    MF_INDEX = "mf_index"
    MF_ELSS = "mf_elss"
    GOLD = "gold"
    FD = "fd"
    PPF = "ppf"
    EPF = "epf"
    NPS = "nps"
    REAL_ESTATE = "real_estate"
    CRYPTO = "crypto"
    CASH = "cash"
    OTHER = "other"


class TxnType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SIP = "sip"
    SWITCH = "switch"


class DataSource(str, enum.Enum):
    YAHOO = "yahoo"
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    POLYGON = "polygon"
    FMP = "fmp"
    MANUAL = "manual"
    REDDIT = "reddit"
    TWITTER = "twitter"
    NEWS_RSS = "news_rss"


class SentimentLabel(str, enum.Enum):
    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"


class JournalAction(str, enum.Enum):
    ENTRY = "entry"
    EXIT = "exit"
    ADD = "add"
    TRIM = "trim"
    HOLD = "hold"
    WATCHLIST = "watchlist"


class ConvictionLevel(str, enum.Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPECULATIVE = "speculative"


# =====================================================================
# LAYER 1 — DATA AGGREGATION
# =====================================================================

class Stock(Base):
    """Master security table."""
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Mutual funds have no short ticker to use as a symbol — the CSV
    # importer falls back to the full fund name (e.g. "CANARA ROBECO ELSS
    # TAX SAVER FUND", 34 chars), so this needs real headroom, not a
    # stock-ticker-sized column.
    symbol: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    exchange: Mapped[str] = mapped_column(String(10), default="NSE")  # NSE, BSE, NASDAQ
    asset_class: Mapped[AssetClassEnum] = mapped_column(Enum(AssetClassEnum))
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    market_cap: Mapped[Optional[float]] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # relationships
    fundamentals: Mapped[list["Fundamental"]] = relationship(back_populates="stock", cascade="all, delete-orphan")
    prices: Mapped[list["PriceHistory"]] = relationship(back_populates="stock", cascade="all, delete-orphan")
    earnings: Mapped[list["EarningsReport"]] = relationship(back_populates="stock", cascade="all, delete-orphan")
    news_items: Mapped[list["NewsItem"]] = relationship(back_populates="stock", cascade="all, delete-orphan")
    sentiments: Mapped[list["SentimentData"]] = relationship(back_populates="stock", cascade="all, delete-orphan")
    insider_trades: Mapped[list["InsiderTrade"]] = relationship(back_populates="stock", cascade="all, delete-orphan")
    positions: Mapped[list["Position"]] = relationship(back_populates="stock", cascade="all, delete-orphan")
    journal_entries: Mapped[list["JournalEntry"]] = relationship(back_populates="stock", cascade="all, delete-orphan")
    research_reports: Mapped[list["ResearchReport"]] = relationship(back_populates="stock", cascade="all, delete-orphan")


class PriceHistory(Base):
    """Daily OHLCV price data."""
    __tablename__ = "price_history"
    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_price_stock_date"),
        Index("ix_price_stock_date", "stock_id", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column(Date)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    adj_close: Mapped[Optional[float]] = mapped_column(Float)
    volume: Mapped[Optional[int]] = mapped_column(Integer)
    source: Mapped[DataSource] = mapped_column(Enum(DataSource), default=DataSource.YAHOO)

    stock: Mapped["Stock"] = relationship(back_populates="prices")


class Fundamental(Base):
    """Quarterly/annual fundamental data — valuation, profitability, debt."""
    __tablename__ = "fundamentals"
    __table_args__ = (
        UniqueConstraint("stock_id", "period_end", "period_type", name="uq_fund_stock_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    period_end: Mapped[date] = mapped_column(Date)
    period_type: Mapped[str] = mapped_column(String(10))  # "quarterly", "annual"

    # Valuation
    pe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    pb_ratio: Mapped[Optional[float]] = mapped_column(Float)
    ps_ratio: Mapped[Optional[float]] = mapped_column(Float)
    ev_ebitda: Mapped[Optional[float]] = mapped_column(Float)
    market_cap: Mapped[Optional[float]] = mapped_column(Float)

    # Profitability
    revenue: Mapped[Optional[float]] = mapped_column(Float)
    net_income: Mapped[Optional[float]] = mapped_column(Float)
    ebitda: Mapped[Optional[float]] = mapped_column(Float)
    gross_margin: Mapped[Optional[float]] = mapped_column(Float)
    operating_margin: Mapped[Optional[float]] = mapped_column(Float)
    net_margin: Mapped[Optional[float]] = mapped_column(Float)
    roe: Mapped[Optional[float]] = mapped_column(Float)
    roce: Mapped[Optional[float]] = mapped_column(Float)
    roa: Mapped[Optional[float]] = mapped_column(Float)

    # Growth
    revenue_growth_yoy: Mapped[Optional[float]] = mapped_column(Float)
    profit_growth_yoy: Mapped[Optional[float]] = mapped_column(Float)
    eps: Mapped[Optional[float]] = mapped_column(Float)
    eps_growth_yoy: Mapped[Optional[float]] = mapped_column(Float)

    # Debt
    total_debt: Mapped[Optional[float]] = mapped_column(Float)
    debt_to_equity: Mapped[Optional[float]] = mapped_column(Float)
    interest_coverage: Mapped[Optional[float]] = mapped_column(Float)
    current_ratio: Mapped[Optional[float]] = mapped_column(Float)

    # Cash
    free_cash_flow: Mapped[Optional[float]] = mapped_column(Float)
    cash_and_equivalents: Mapped[Optional[float]] = mapped_column(Float)

    # Dividend
    dividend_yield: Mapped[Optional[float]] = mapped_column(Float)
    payout_ratio: Mapped[Optional[float]] = mapped_column(Float)

    source: Mapped[DataSource] = mapped_column(Enum(DataSource), default=DataSource.YAHOO)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    stock: Mapped["Stock"] = relationship(back_populates="fundamentals")


class EarningsReport(Base):
    """Quarterly earnings reports with key highlights."""
    __tablename__ = "earnings_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    quarter: Mapped[str] = mapped_column(String(10))  # "Q1FY25"
    report_date: Mapped[date] = mapped_column(Date)

    revenue: Mapped[Optional[float]] = mapped_column(Float)
    net_income: Mapped[Optional[float]] = mapped_column(Float)
    eps_actual: Mapped[Optional[float]] = mapped_column(Float)
    eps_estimate: Mapped[Optional[float]] = mapped_column(Float)
    revenue_estimate: Mapped[Optional[float]] = mapped_column(Float)

    beat_eps: Mapped[Optional[bool]] = mapped_column(Boolean)
    beat_revenue: Mapped[Optional[bool]] = mapped_column(Boolean)
    surprise_pct: Mapped[Optional[float]] = mapped_column(Float)

    # AI-generated fields (Layer 2)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    management_guidance: Mapped[Optional[str]] = mapped_column(Text)
    risk_factors: Mapped[Optional[str]] = mapped_column(Text)
    key_highlights: Mapped[Optional[dict]] = mapped_column(JSONB)

    source: Mapped[DataSource] = mapped_column(Enum(DataSource), default=DataSource.FMP)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    stock: Mapped["Stock"] = relationship(back_populates="earnings")


class MacroIndicator(Base):
    """Macro-economic indicators — rates, inflation, GDP, etc."""
    __tablename__ = "macro_indicators"
    __table_args__ = (
        UniqueConstraint("indicator", "date", name="uq_macro_indicator_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    indicator: Mapped[str] = mapped_column(String(50), index=True)  # "repo_rate", "cpi_india", "us_10y"
    date: Mapped[date] = mapped_column(Date)
    value: Mapped[float] = mapped_column(Float)
    country: Mapped[str] = mapped_column(String(5), default="IN")
    source: Mapped[DataSource] = mapped_column(Enum(DataSource), default=DataSource.MANUAL)
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class NewsItem(Base):
    """News articles and their sentiment."""
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stocks.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    source_name: Mapped[Optional[str]] = mapped_column(String(100))
    content_snippet: Mapped[Optional[str]] = mapped_column(Text)

    # AI-enriched
    sentiment: Mapped[Optional[SentimentLabel]] = mapped_column(Enum(SentimentLabel))
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # -1 to +1
    relevance_score: Mapped[Optional[float]] = mapped_column(Float)  # 0 to 1
    summary: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[list]] = mapped_column(JSONB)

    source: Mapped[DataSource] = mapped_column(Enum(DataSource), default=DataSource.NEWS_RSS)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    stock: Mapped[Optional["Stock"]] = relationship(back_populates="news_items")


class SentimentData(Base):
    """Reddit/X/social sentiment aggregation."""
    __tablename__ = "sentiment_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stocks.id", ondelete="SET NULL"), index=True)
    platform: Mapped[str] = mapped_column(String(20))  # "reddit", "twitter", "stocktwits"
    date: Mapped[date] = mapped_column(Date)

    mentions: Mapped[int] = mapped_column(Integer, default=0)
    bullish_count: Mapped[int] = mapped_column(Integer, default=0)
    bearish_count: Mapped[int] = mapped_column(Integer, default=0)
    neutral_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_sentiment_score: Mapped[Optional[float]] = mapped_column(Float)
    top_posts: Mapped[Optional[list]] = mapped_column(JSONB)  # [{title, url, score, sentiment}]

    source: Mapped[DataSource] = mapped_column(Enum(DataSource))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    stock: Mapped[Optional["Stock"]] = relationship(back_populates="sentiments")


class InsiderTrade(Base):
    """Insider / promoter trading activity."""
    __tablename__ = "insider_trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    insider_name: Mapped[str] = mapped_column(String(200))
    designation: Mapped[Optional[str]] = mapped_column(String(100))
    trade_type: Mapped[str] = mapped_column(String(10))  # "buy", "sell"
    trade_date: Mapped[date] = mapped_column(Date)
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    value: Mapped[float] = mapped_column(Float)

    source: Mapped[DataSource] = mapped_column(Enum(DataSource), default=DataSource.FMP)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    stock: Mapped["Stock"] = relationship(back_populates="insider_trades")


# =====================================================================
# LAYER 2 — RESEARCH ENGINE
# =====================================================================

class ResearchReport(Base):
    """AI-generated research reports per stock."""
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    report_type: Mapped[str] = mapped_column(String(50))  # "earnings_summary", "moat_analysis", "debt_risk", "quality_score"
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Structured output
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    scores: Mapped[Optional[dict]] = mapped_column(JSONB)
    # e.g. {"moat_score": 7, "growth_consistency": 8, "debt_risk": 3, "business_quality": "A"}

    risk_factors: Mapped[Optional[list]] = mapped_column(JSONB)
    key_metrics: Mapped[Optional[dict]] = mapped_column(JSONB)
    model_used: Mapped[Optional[str]] = mapped_column(String(50))
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100))  # ChromaDB reference

    stock: Mapped["Stock"] = relationship(back_populates="research_reports")


# =====================================================================
# LAYER 3 — PORTFOLIO DECISION SYSTEM
# =====================================================================

class Position(Base):
    """Current portfolio positions with decision metadata."""
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("stock_id", name="uq_position_stock"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)

    # Position data
    quantity: Mapped[float] = mapped_column(Float, default=0)
    avg_buy_price: Mapped[float] = mapped_column(Float, default=0)
    current_price: Mapped[Optional[float]] = mapped_column(Float)
    invested_amount: Mapped[float] = mapped_column(Float, default=0)
    current_value: Mapped[Optional[float]] = mapped_column(Float)

    # Allocation
    target_allocation_pct: Mapped[Optional[float]] = mapped_column(Float)  # what % of portfolio it should be
    actual_allocation_pct: Mapped[Optional[float]] = mapped_column(Float)

    # Decision metadata (Layer 3)
    conviction: Mapped[Optional[ConvictionLevel]] = mapped_column(Enum(ConvictionLevel))
    thesis: Mapped[Optional[str]] = mapped_column(Text)  # why you own this
    expected_return_pct: Mapped[Optional[float]] = mapped_column(Float)  # your base-case expected return
    risk_reward_ratio: Mapped[Optional[float]] = mapped_column(Float)
    stop_loss_pct: Mapped[Optional[float]] = mapped_column(Float)
    target_price: Mapped[Optional[float]] = mapped_column(Float)
    time_horizon_months: Mapped[Optional[int]] = mapped_column(Integer)

    # Risk
    max_drawdown_pct: Mapped[Optional[float]] = mapped_column(Float)
    beta: Mapped[Optional[float]] = mapped_column(Float)
    sector_weight_pct: Mapped[Optional[float]] = mapped_column(Float)

    # Invalidation
    invalidation_conditions: Mapped[Optional[list]] = mapped_column(JSONB)
    # e.g. ["revenue drops >20% YoY", "promoter sells >5%", "debt-to-equity crosses 2"]

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    entry_date: Mapped[Optional[date]] = mapped_column(Date)
    exit_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    stock: Mapped["Stock"] = relationship(back_populates="positions")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="position", cascade="all, delete-orphan")


class Transaction(Base):
    """Individual buy/sell/SIP transactions."""
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id", ondelete="CASCADE"), index=True)
    txn_type: Mapped[TxnType] = mapped_column(Enum(TxnType))
    date: Mapped[date] = mapped_column(Date)
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    charges: Mapped[float] = mapped_column(Float, default=0)
    amount: Mapped[float] = mapped_column(Float)  # quantity * price + charges
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    position: Mapped["Position"] = relationship(back_populates="transactions")


class PortfolioSnapshot(Base):
    """Daily portfolio snapshots for tracking over time."""
    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    total_invested: Mapped[float] = mapped_column(Float)
    total_value: Mapped[float] = mapped_column(Float)
    total_pnl: Mapped[float] = mapped_column(Float)
    total_pnl_pct: Mapped[float] = mapped_column(Float)
    cagr: Mapped[Optional[float]] = mapped_column(Float)
    xirr: Mapped[Optional[float]] = mapped_column(Float)

    # Allocation snapshot
    allocation_by_class: Mapped[Optional[dict]] = mapped_column(JSONB)
    allocation_by_sector: Mapped[Optional[dict]] = mapped_column(JSONB)
    top_holdings: Mapped[Optional[list]] = mapped_column(JSONB)

    # Risk metrics
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    concentration_top5_pct: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# =====================================================================
# LAYER 4 — DECISION JOURNAL
# =====================================================================

class JournalEntry(Base):
    """Investment decision journal — the most important table."""
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stocks.id", ondelete="SET NULL"), index=True)
    action: Mapped[JournalAction] = mapped_column(Enum(JournalAction))
    date: Mapped[date] = mapped_column(Date, default=date.today)

    # --- Entry Rationale ---
    why: Mapped[str] = mapped_column(Text)  # Why did you enter/exit?
    thesis: Mapped[Optional[str]] = mapped_column(Text)  # Core investment thesis
    assumptions: Mapped[Optional[list]] = mapped_column(JSONB)
    # e.g. ["Revenue will grow 30%+ for 3 years", "Sector tailwinds from PLI scheme"]

    expected_catalyst: Mapped[Optional[str]] = mapped_column(Text)
    # e.g. "Q3 earnings beat, new order wins"

    risk_factors: Mapped[Optional[list]] = mapped_column(JSONB)
    # e.g. ["High valuation PE>50", "Promoter pledge 15%"]

    invalidation_conditions: Mapped[Optional[list]] = mapped_column(JSONB)
    # e.g. ["If revenue growth <10% for 2 quarters", "If debt-to-equity >2"]

    time_horizon: Mapped[Optional[str]] = mapped_column(String(50))  # "3-5 years", "6-12 months"
    conviction: Mapped[Optional[ConvictionLevel]] = mapped_column(Enum(ConvictionLevel))

    # --- Trade Details ---
    quantity: Mapped[Optional[float]] = mapped_column(Float)
    price: Mapped[Optional[float]] = mapped_column(Float)
    position_size_pct: Mapped[Optional[float]] = mapped_column(Float)  # % of portfolio

    # --- Review (filled later) ---
    outcome: Mapped[Optional[str]] = mapped_column(Text)  # What actually happened
    what_went_right: Mapped[Optional[str]] = mapped_column(Text)
    what_went_wrong: Mapped[Optional[str]] = mapped_column(Text)
    bias_identified: Mapped[Optional[str]] = mapped_column(Text)
    # e.g. "anchoring bias — held too long because of buy price"

    lesson_learned: Mapped[Optional[str]] = mapped_column(Text)
    rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-10 self-grade on decision quality

    review_date: Mapped[Optional[date]] = mapped_column(Date)
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

    # --- Tags ---
    tags: Mapped[Optional[list]] = mapped_column(JSONB)
    # e.g. ["momentum", "value", "turnaround", "compounder"]

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    stock: Mapped[Optional["Stock"]] = relationship(back_populates="journal_entries")
