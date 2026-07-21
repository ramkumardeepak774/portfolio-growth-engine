# Portfolio Growth Engine — Roadmap

> Track what's built, what's in progress, and what's next.

---

## Status Legend

| Symbol | Meaning |
|---|---|
| ✅ | Done |
| 🚧 | In Progress |
| 📋 | Planned |
| ❌ | Dropped / Won't Do |

---

## Phase 1 — Foundation (Done ✅)

- [x] FastAPI backend with 4 API layers (data, research, portfolio, journal)
- [x] Portfolio model (holdings, transactions, asset classes)
- [x] Financial calculations: CAGR, XIRR, Alpha, Beta, Sharpe, Volatility, Max Drawdown
- [x] Asset allocation & rebalancing engine
- [x] Goal tracker
- [x] Decision journal (document reasoning before trades)
- [x] Market data via Yahoo Finance (yfinance)
- [x] CLI interface
- [x] Docker Compose setup

---

## Phase 2 — Frontend Dashboard (Done ✅)

- [x] Next.js 16 + TypeScript + Tailwind CSS v4
- [x] Login page with JWT auth + demo mode
- [x] Dashboard — KPI cards (portfolio value, CAGR, XIRR, beta, Sharpe, drawdown)
- [x] Portfolio vs NIFTY 50 benchmark chart
- [x] Sector allocation pie chart
- [x] Drawdown chart
- [x] Rule-based portfolio insights
- [x] Holdings table with P&L and search
- [x] Analytics page with tooltips explaining each metric
- [x] Rebalancing suggestions UI
- [x] Decision journal UI (create + view entries)
- [x] Settings page (API URL, theme toggle)
- [x] Dark/light theme
- [x] Responsive design
- [x] Pushed to GitHub
- [x] **Frontend integrated with FastAPI backend**

---

## Phase 3 — Testing (Done ✅)

### Backend (pytest)
- [x] `tests/` folder setup with pytest + pytest-asyncio
- [x] Unit tests for financial calculations (CAGR, XIRR, Max Drawdown, Beta, Alpha, Sharpe)
- [x] Unit tests for portfolio P&L and allocation
- [x] API integration tests (portfolio summary, holdings, allocation routes)
- [x] `pyproject.toml` updated with pytest config

### Frontend (Vitest)
- [x] Vitest setup in `frontend/`
- [x] Unit tests for `lib/financial.ts` (mirrors backend math)
- [x] Unit tests for `lib/format.ts` (INR formatting edge cases)

### CI/CD
- [x] GitHub Actions workflow — run backend + frontend tests on every push

---

## Phase 4 — Data & Analytics (In Progress 🚧)

- [x] PostgreSQL integration for price caching — `src/price_cache.py`, Postgres-first with a live-Yahoo fallback if the DB is unreachable
- [x] Neon PostgreSQL deployment (free tier)
- [x] Historical portfolio value reconstruction from transactions — `analyzer.portfolio_value_series()`
- [x] Real portfolio growth chart (not just proxy from top holding) — dashboard's growth/drawdown/benchmark charts and Beta/Alpha/Sharpe/Volatility tiles all use the real series now. Direct-equity holdings only for now — mutual funds/gold/FD/etc. have no reliable daily price series, so they're excluded from the reconstructed value (documented in `analyzer._PRICEABLE_ASSET_CLASSES`)
- [ ] Benchmark price cache (NIFTY 50, NIFTY Next 50, SENSEX) — NIFTY 50 fetch is still live/uncached
- [ ] XIRR calculation from actual transaction history on frontend
- [ ] Monthly returns heatmap (calendar view)
- [ ] Rolling returns chart (1Y, 3Y, 5Y rolling CAGR)

---

## Phase 4 — Portfolio Management UI (In Progress 🚧)

- [x] Migrate portfolio storage from YAML to Postgres — `src/db_portfolio.py`,
      DB-first reads with a YAML fallback, using the `Stock`/`Position`/
      `Transaction` tables that already existed in `src/db/models.py` but
      sat unused. One-time seed script: `scripts/seed_portfolio_from_yaml.py`
- [x] Add transactions from UI (buy, sell, SIP, dividend, switch) —
      `POST /api/portfolio/transactions`, "Add Transaction" button on the
      Holdings page. Same endpoint creates a brand-new holding if the
      symbol doesn't exist yet (name/asset_class required in that case)
- [ ] Edit/delete holdings and transactions from UI
- [ ] Import transactions from CSV (Zerodha, Groww format)
- [ ] Holdings sorted by various columns
- [ ] Holding detail page (full transaction history, price chart, fundamentals)
- [ ] SIP tracker — are your SIPs on schedule?

---

## Phase 5 — Deployment (Done ✅)

- [x] Deploy frontend to Vercel — https://frontend-three-lime-80.vercel.app
- [x] Deploy backend to Railway — https://api-production-82d5.up.railway.app
- [x] Setup Neon PostgreSQL — provisioned, not yet wired into the app (Phase 4)
- [x] Environment variables configured on Vercel
- [x] CORS updated for production URL (env-driven via `CORS_ORIGINS`, no code change needed going forward)
- [ ] Custom domain (optional)

Gaps surfaced during deployment — now closed (see Phase 5.1 below):
- ~~No backend auth endpoint~~
- ~~Every `/api/*` backend route is fully public~~

---

## Phase 5.1 — Backend Auth (Done ✅)

- [x] `POST /auth/token` — JWT login (`src/auth.py`, `src/api/auth_routes.py`)
- [x] Every `/api/*` route requires a valid bearer token
- [x] Password hashed with bcrypt; dev defaults documented, must be
      overridden in production (`AUTH_USERNAME`, `AUTH_PASSWORD_HASH`,
      `JWT_SECRET_KEY` env vars)
- [x] Frontend login form works end-to-end against the real endpoint (it was
      already correctly wired, just had nothing to call)
- [x] 18 new tests: password hashing, token creation/validation, `/auth/token`
      success/failure, protected-route gating

---

## Phase 6 — Advanced Analytics (Future 📋)

- [ ] Rolling beta chart
- [ ] Correlation matrix across holdings
- [ ] Sector rotation visualization
- [ ] Goal scenario planner (what if I invest X more per month?)
- [ ] SIP vs lump sum comparison calculator
- [ ] Tax P&L report (STCG / LTCG breakdown)
- [ ] Portfolio stress test (what happens in a 30% crash?)

---

## Ideas Parking Lot

> Things to consider later — not committed yet

- Watchlist with price alerts
- Earnings calendar for held stocks
- Dividend tracker
- Mutual fund overlap checker
- Compare two portfolios side by side
- Export to PDF / Excel

---

## Dropped

- ❌ AI/LLM research features (overengineered for MVP)
- ❌ Redis + Kafka + vector DB (unnecessary complexity)
- ❌ Kubernetes / microservices (overkill for personal use)
- ❌ 1000x goal (unrealistic — replaced with 20x/16% CAGR)
