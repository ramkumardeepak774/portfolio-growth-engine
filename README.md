# Portfolio Growth Engine

> **Primary Goal:** Build a modern portfolio analytics and investment research platform that helps users track portfolio performance, compare against market benchmarks, analyze risk-adjusted returns, and make data-driven investment decisions through clean visual analytics and financial metrics.

---

## Goal

Build long-term wealth through disciplined investing, data-driven decisions, and compounding.

$$\text{20x in 20 years} \Rightarrow \text{CAGR} = \left(\frac{20}{1}\right)^{\frac{1}{20}} - 1 \approx 16.2\%$$

| Target | CAGR Required | Realistic Assessment |
|---|---|---|
| 5x | 8.4% | Conservative — achievable with debt + equity mix |
| 10x | 12.2% | Realistic — index funds + stay invested long enough |
| 20x | 16.2% | Achievable — diversified equity with discipline |
| 50x | 21.5% | Difficult — requires good stock selection + low churn |
| 100x | 25.9% | Very hard — sustained outperformance over 20 years |

**Realistic target: 15–20x in 20 years (15–16% CAGR)** — in line with long-term Indian equity market returns. Beating the index consistently by even 2–3% per year is genuinely difficult and puts you in the top tier of investors.

This platform helps you stay disciplined, measure accurately, and make better decisions — the real drivers of long-term wealth.

---

## What This Platform Does

### Analytics Engine
- **CAGR** — Compound Annual Growth Rate across full portfolio and per holding
- **XIRR** — Time-weighted return for irregular cashflows (SIPs, lump sums)
- **Alpha** — Excess return vs NIFTY 50 after adjusting for beta
- **Beta** — Market sensitivity coefficient
- **Sharpe Ratio** — Risk-adjusted return (return per unit of risk)
- **Volatility** — Annualised standard deviation of daily returns
- **Maximum Drawdown** — Worst peak-to-trough decline

### Portfolio Management
- Track stocks, mutual funds, gold, FDs, PPF, NPS, real estate, crypto
- Transaction history (buy, sell, SIP, dividend, switch)
- Sector and asset class allocation breakdown
- Concentration risk analysis (HHI, top-3/top-5 weight)
- Rebalancing suggestions based on target allocation

### Benchmark Comparison
- Compare portfolio against NIFTY 50, NIFTY Next 50, SENSEX
- Indexed growth chart (portfolio vs benchmark)
- Alpha generation tracking over time

### Goal Tracker
- Define custom financial goals with target multiplier and time horizon
- Track actual CAGR vs required CAGR
- Scenario modelling — what CAGR do you need from today to hit the target?

### Decision Journal
- Document investment reasoning **before** executing trades
- Record risk factors, invalidation conditions, time horizon, conviction level
- Review past decisions — what went right, what went wrong, what bias you had
- Track rating and outcome to improve decision quality over time

### Market Data
- Live price fetching via Yahoo Finance (yfinance)
- Historical price caching in PostgreSQL
- Fundamentals: P/E, P/B, ROE, debt/equity, revenue growth
- News and Reddit sentiment (optional)

---

## Architecture

```
portfolio-growth-engine/
│
├── src/                          # FastAPI backend
│   ├── app.py                    # Application entry point
│   ├── models.py                 # Domain models (Holding, Transaction, Portfolio)
│   ├── analyzer.py               # Financial calculations engine
│   ├── allocator.py              # Asset allocation & rebalancing
│   ├── goal_tracker.py           # Goal progress tracking
│   ├── screener.py               # Stock/MF screening
│   ├── decisions.py              # Risk validation
│   ├── journal.py                # Decision journal management
│   ├── reports.py                # Report generation
│   │
│   ├── api/                      # REST API layer
│   │   ├── portfolio_routes.py   # /api/portfolio/*
│   │   ├── data_routes.py        # /api/data/*
│   │   ├── journal_routes.py     # /api/journal/*
│   │   └── research_routes.py    # /api/research/*
│   │
│   ├── collectors/               # Market data collectors
│   │   ├── yahoo_collector.py    # Yahoo Finance (primary)
│   │   ├── finnhub_collector.py  # Finnhub (news)
│   │   ├── fmp_collector.py      # Financial Modeling Prep
│   │   ├── news_collector.py     # Financial news
│   │   └── reddit_collector.py   # Reddit sentiment
│   │
│   └── db/                       # Database layer
│       ├── engine.py             # SQLAlchemy engine
│       └── models.py             # ORM models
│
├── frontend/                     # Next.js dashboard
│   ├── app/
│   │   ├── (auth)/login/         # Login page
│   │   └── (dashboard)/          # Protected dashboard
│   │       ├── dashboard/        # KPIs, charts, insights
│   │       ├── holdings/         # Holdings table
│   │       ├── analytics/        # Risk metrics
│   │       ├── journal/          # Decision journal
│   │       └── settings/         # Configuration
│   │
│   ├── components/
│   │   ├── charts/               # Recharts wrappers
│   │   ├── dashboard/            # KPI cards, insights
│   │   └── layout/               # Sidebar, header
│   │
│   ├── lib/
│   │   ├── api.ts                # Axios client + JWT
│   │   ├── financial.ts          # Client-side calculations
│   │   └── format.ts             # INR/% formatting
│   │
│   └── services/                 # Typed API service layer
│
├── data/
│   ├── portfolio.yaml            # Holdings definition
│   ├── goals.yaml                # Financial goals
│   └── journal/                  # Decision journal entries
│
└── notebooks/
    └── portfolio_analysis.ipynb  # Exploratory analysis
```

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Language | Python 3.11+ |
| Data | yfinance, pandas, numpy |
| Financial math | pyxirr |
| Task queue | Celery + Redis (optional) |
| Database | PostgreSQL / SQLite |
| ORM | SQLAlchemy |

### Frontend
| Layer | Technology |
|---|---|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript (strict) |
| Styling | Tailwind CSS v4 + shadcn/ui |
| Charts | Recharts |
| Data fetching | TanStack Query v5 |
| HTTP | Axios + JWT interceptors |
| Theme | Dark-first (next-themes) |

### Hosting (₹0/month)
| Service | Provider |
|---|---|
| Frontend | Vercel (free tier) |
| Backend | Railway / Render (free tier) |
| Database | Neon PostgreSQL (free tier) |

---

## Quick Start

### Backend

```bash
# 1. Install dependencies (uv creates .venv and installs everything, incl. dev/test deps)
uv sync --extra dev

# 2. Configure environment
cp .env.example .env
# Add API keys if needed (Yahoo Finance is free, no key required)

# 3. Add your holdings
vim data/portfolio.yaml

# 4. Start the API server
uv run uvicorn src.app:app --reload --port 8000
# API docs at http://localhost:8000/docs

# 5. Run the test suite
uv run pytest -v
```

> No `uv`? Install it with `brew install uv` (or see [astral.sh/uv](https://astral.sh/uv)). Prefer plain pip? `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"` works too.

### CLI (no frontend needed)

```bash
uv run python -m src.cli summary       # Portfolio summary
uv run python -m src.cli goal          # Goal progress
uv run python -m src.cli rebalance     # Rebalancing suggestions
uv run python -m src.cli screen        # Stock screener
uv run python -m src.cli report        # Full report
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
# Set NEXT_PUBLIC_AUTH_DISABLED=true (for local dev)

npm run dev
# Open http://localhost:3000
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/portfolio/summary` | Portfolio KPIs (CAGR, XIRR, total value) |
| GET | `/api/portfolio/holdings` | Per-holding performance table |
| GET | `/api/portfolio/allocation` | Sector & asset class breakdown |
| GET | `/api/portfolio/rebalance` | Rebalancing action plan |
| GET | `/api/portfolio/goals` | Goal progress tracking |
| GET | `/api/data/prices/{symbol}` | Historical prices (Yahoo Finance) |
| GET | `/api/data/fundamentals/{symbol}` | Fundamental data |
| GET | `/api/journal/entries` | Decision journal entries |
| POST | `/api/journal/entry` | Create new journal entry |
| POST | `/api/journal/review/{id}` | Review a past decision |
| GET | `/health` | Health check |

Full interactive docs at `/docs` (Swagger UI).

---

## Financial Calculations

All math is implemented from first principles in `src/analyzer.py` (backend) and `frontend/lib/financial.ts` (client):

| Metric | Formula |
|---|---|
| CAGR | $(FV / PV)^{1/n} - 1$ |
| XIRR | Newton-Raphson on $\sum \frac{C_i}{(1+r)^{t_i}} = 0$ |
| Volatility | $\sigma_{daily} \times \sqrt{252}$ |
| Max Drawdown | $\max\left(\frac{Peak - Trough}{Peak}\right)$ |
| Beta | $\frac{Cov(P, B)}{Var(B)}$ |
| Alpha | $R_P - [R_f + \beta \times (R_B - R_f)]$ |
| Sharpe | $\frac{R_P - R_f}{\sigma_P}$ (Rf = 6.5% India 10yr G-Sec) |

---

## Deployment

### 1. Frontend → Vercel

```bash
# Push to GitHub, then import on vercel.com
# Set environment variable:
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### 2. Backend → Railway

```bash
# Connect GitHub repo on railway.app
# Add environment variables
# Railway auto-detects Python and runs uvicorn
```

### 3. Update CORS

In `src/app.py`, add your Vercel URL:
```python
allow_origins=["https://your-app.vercel.app"]
```

---

## Portfolio Data Format

```yaml
# data/portfolio.yaml
holdings:
  - symbol: RELIANCE.NS
    name: Reliance Industries
    asset_class: equity_large_cap
    sector: Energy
    transactions:
      - date: 2023-01-15
        type: buy
        quantity: 10
        price: 2500.00
        charges: 25.00

goals:
  target_multiplier: 1000
  target_years: 20
```

---

## Contributing

This is a personal project. Feel free to fork and adapt for your own portfolio.

---

## License

MIT — use freely, invest wisely.

---

*Built for the Indian market. All calculations in INR. Not financial advice.*
