# Sprint Log

> One entry per week. What was planned, what got done, what's blocked.

---

## Week 1 — 17 May 2026

### Goal
Build and ship the frontend dashboard, push to GitHub.

### Done ✅
- Built full Next.js 16 frontend from scratch
  - Login page (JWT + demo bypass)
  - Dashboard (KPI cards, benchmark chart, sector pie, drawdown, insights)
  - Holdings page (table, search, P&L)
  - Analytics page (8 metrics with tooltips, rebalancing suggestions)
  - Decision Journal (create entries, conviction/action badges)
  - Settings (API URL config, theme toggle)
- TypeScript — zero compile errors, clean production build
- Finance math: CAGR, XIRR, Alpha, Beta, Sharpe, Volatility, Max Drawdown
- Dark theme with finance-terminal colour palette
- Set up GitHub repo (personal account: ramkumardeepak774)
- Pushed all 99 files to GitHub

### Blocked / Pending
- PostgreSQL not connected (price data uses live Yahoo Finance calls)
- Holdings data is still YAML-based, no UI write support yet

### Done Later in Week ✅
- Frontend successfully integrated with FastAPI backend

### Next Week
- Deploy backend to Railway
- Deploy frontend to Vercel
- Connect Neon PostgreSQL for price caching

---

## Week 2 — 20 Jul 2026

### Goal
Phase 3 testing — pytest (backend), Vitest (frontend), GitHub Actions CI.

### Done ✅
- Backend: `tests/` folder with pytest + pytest-asyncio, `pyproject.toml` pytest config
  - 60 unit tests: `test_analyzer.py` (CAGR, XIRR, allocation, concentration), `test_allocator.py` (rebalancing, age-based allocation), `test_models.py` (Holding/Portfolio/Goal properties)
  - 8 API integration tests (`test_api_portfolio.py`) via FastAPI `TestClient` — summary, holdings, allocation, rebalance, goals
  - Fixed a pre-existing bug: `src/db/engine.py` had a bad relative import (`.config` instead of `..config`) that broke `from src.app import app` entirely
- Frontend: Vitest installed and configured (`frontend/vitest.config.ts`), `npm test` / `npm run test:watch` scripts
  - 57 unit tests: `lib/financial.test.ts` (CAGR, XIRR, volatility, drawdown, Sharpe, Beta, Alpha, insights) and `lib/format.test.ts` (INR formatting, percentages, dates, ratios)
- CI: `.github/workflows/test.yml` — runs backend pytest and frontend vitest in parallel jobs on every push/PR to main

### Blocked / Pending
- None — 68 backend + 57 frontend tests passing

### Next Week
- Deploy backend to Railway, frontend to Vercel
- Connect Neon PostgreSQL for price caching

---

## Week 3 — 21 Jul 2026

### Goal
Phase 5 — deploy backend to Railway, frontend to Vercel, provision Neon.

### Done ✅
- Installed and authenticated Vercel, Railway, and Neon CLIs
- Created Neon Postgres project (`portfolio-growth-engine`, PG 17, us-east-1) — connection string captured, not yet wired into the app
- Made backend CORS env-driven (`CORS_ORIGINS` in `src/config.py`/`src/app.py`) instead of hardcoded, so future frontend URL changes don't need a code change
- Added `railway.json` with an explicit `uv run uvicorn` start command and `/health` healthcheck — Railway's builder can't infer a FastAPI entrypoint on its own
- Fixed `frontend/vercel.json` — it referenced `NEXT_PUBLIC_API_URL` via the legacy `@api_url` secrets syntax, which would never have resolved
- Deployed backend to Railway: https://api-production-82d5.up.railway.app (linked to GitHub `main` for auto-deploy on push)
- Deployed frontend to Vercel: https://frontend-three-lime-80.vercel.app
- Verified CORS end-to-end (Vercel origin gets `access-control-allow-origin` back from Railway)
- Caught and removed a mistake before it shipped: `NEXT_PUBLIC_AUTH_DISABLED=true` should never be set in production — briefly set it, then reverted

### Blocked / Pending
- No backend auth endpoint exists (`/auth/token`) — frontend's real login form fails; "Continue with demo data" is the only working path in production
- Every backend `/api/*` route is unauthenticated — anyone with the Railway URL can read live portfolio data
- Neon Postgres is provisioned but unused — app still hits Yahoo Finance live on every request

### Next Week
- Wire Neon Postgres into the app for price caching (Phase 4)
- Decide on and implement backend auth before this goes any further

---

## Week 4 — 21 Jul 2026

### Goal
Fix the dashboard's growth/benchmark/drawdown charts and Beta/Alpha/Sharpe/
Volatility — all of them were secretly built off a single top holding's
price series standing in for the whole portfolio. Wire in Neon Postgres for
price caching while doing it.

### Done ✅
- `analyzer.portfolio_value_series()` reconstructs real weighted portfolio
  value over time from transaction history (quantity-at-date) × cached
  Yahoo prices — direct-equity holdings only, documented limitation
- `src/price_cache.py` — Postgres-backed price cache using the existing
  (previously unused) `Stock`/`PriceHistory` ORM models, bulk upsert via
  `ON CONFLICT`, falls back to a live uncached Yahoo fetch if Postgres is
  unreachable
- New `GET /api/portfolio/growth?period=` endpoint
- Dashboard rewired: growth chart, benchmark-vs-NIFTY chart, drawdown
  chart, and Beta/Alpha/Sharpe/Volatility tiles all consume the real
  series now instead of one holding's price history
- Caught and fixed a serious perf bug before it shipped: `get_sync_engine()`
  created a brand-new engine + connection **per call**, and since the
  growth endpoint calls it once per holding, a cold-cache request took
  4m17s against Neon. Caching the engine (`@lru_cache`) brought it to ~7s
- 9 new tests: 6 for `portfolio_value_series()` (mocked price source, no
  network), 3 for the growth endpoint (auth gate, validation, mocked
  series) — full suite green (95 backend + 57 frontend passing)

### Blocked / Pending
- Growth endpoint is ~6-7s even warm — acceptable for a personal dashboard
  but not fast; further optimization (parallel per-holding fetches) would
  help if this becomes annoying
- NIFTY 50 benchmark data is still fetched live/uncached every time
- Mutual funds, gold, FD/PPF/EPF/NPS, real estate excluded from the value
  series entirely (no reliable daily price source) — portfolio_value only
  reflects direct equity holdings, not the true multi-asset total

### Next Week
- Decide whether mutual fund NAV history is worth sourcing for the value
  series, or leave it equity-only long-term
- Backlog: CSV import, UI-based transaction entry, monthly returns heatmap

---

<!-- Copy this template for each new week -->
<!--
## Week N — DD MMM YYYY

### Goal


### Done ✅
-

### Blocked / Pending
-

### Next Week
-
-->
