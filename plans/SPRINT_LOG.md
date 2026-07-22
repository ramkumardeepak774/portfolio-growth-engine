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

## Week 5 — 21 Jul 2026

### Goal
Add transaction entry from the UI — closing out the last High Priority
backlog item.

### Done ✅
- Migrated portfolio storage from YAML to Postgres. The `Stock`/`Position`/
  `Transaction` tables already existed in `src/db/models.py` but nothing
  used them — same pattern as the price-cache tables two weeks ago.
  `src/db_portfolio.py` reads DB-first with a YAML fallback (so tests/CI
  without a reachable Postgres keep working unchanged — verified both with
  and without a local `.env`, 4.9s vs 71s+ depending on whether Neon is
  actually reachable)
- One-time seed script (`scripts/seed_portfolio_from_yaml.py`, idempotent)
  — ran it against the real Neon DB, all 9 real holdings migrated and
  verified byte-for-byte matching (`total_invested`/`total_value`/
  `holdings_count` identical before and after)
- `POST /api/portfolio/transactions` — records a buy/sell/SIP/dividend/
  switch, creates the Stock+Position if the symbol is new (400 if
  name/asset_class missing in that case), 503 if Postgres is unreachable
  (no silent YAML fallback for writes — a write that didn't persist
  should never look like it succeeded)
- Wired up the "Add Transaction" form on the Holdings page (previously a
  non-functional UI stub that just told users to hand-edit the YAML file)
- 16 new backend tests (111 total) — mocked-session tests for
  `add_transaction()`/`load_portfolio_from_db()` since a real SQLite
  integration test isn't viable (the shared `Stock` model has a
  Postgres-only JSONB column SQLite can't compile), plus API-level tests
  for the new endpoint
- Full write→read→cleanup cycle smoke-tested against the real Neon DB
  three times (once per server session) — each time verified the DB
  returned to its exact original state afterward

### Blocked / Pending
- Edit/delete holdings and transactions still needs UI
- Goals are still YAML-only (not migrated — rarely edited, out of scope)
- CSV import (Zerodha/Groww format) not started

### Next Week
- Medium priority backlog: CSV import, monthly returns heatmap, rolling
  returns chart, holding detail page, tax P&L report

---

## Week 5.1 — 22 Jul 2026

### Goal
Actually fix the Railway auto-deploy issue instead of nudging it manually
after every merge (docs/growth-chart/transactions merges all needed a
manual `railway up`).

### Done ✅
- Root cause: Railway's "Auto Deploy" setting under Service Settings →
  Source is a dashboard-only toggle, invisible and unsettable via the CLI
  or any API endpoint reachable with a personal token — same shape of
  problem as the Vercel GitHub App install gap from two weeks ago. It was
  off; turned on manually via the dashboard.
- This commit is itself the test: if Railway auto-deploys it without a
  manual `railway up`, the fix holds.
- **Update: the dashboard toggle didn't fix it either.** Verified with a
  real merge — 3+ minutes, no auto-deploy triggered. Gave up on Railway's
  own GitHub integration entirely.
- Real fix: added a `deploy-backend` job to `.github/workflows/test.yml`
  that runs `railway up` after `backend`/`frontend` tests pass, only on
  pushes to `main`. Deploys are now triggered by our own CI (which has
  never once missed a run all session) instead of Railway's flaky
  webhook. `RAILWAY_TOKEN` (a project-scoped token, not an account
  token) added as a GitHub Actions secret.

### Next Week
- Medium priority backlog: CSV import, monthly returns heatmap, rolling
  returns chart, holding detail page, tax P&L report

---

## Week 6 — 22 Jul 2026

### Goal
CSV import from Zerodha, closing out the Railway deploy saga first.

### Done ✅
- Railway auto-deploy: dashboard toggle didn't fix it either (verified
  with a real merge, 3+ min, nothing triggered). Gave up on Railway's own
  GitHub integration entirely — deploys now run from our own CI
  (`deploy-backend` job in `.github/workflows/test.yml`, `railway up`
  after tests pass, project-scoped `RAILWAY_TOKEN` secret). First attempt
  failed too (`curl | sh` choked on the installer's bash syntax under
  POSIX dash) — fixed with `| bash`. Confirmed working end-to-end on the
  next real merge: push → tests → deploy → live, zero manual intervention.
- `POST /api/portfolio/import/csv` — bulk-import from a Zerodha Kite
  Holdings export (Console → Portfolio → Holdings → Download). This is a
  current-snapshot export with no trade dates, so each row becomes one
  synthetic buy transaction dated today at average cost (LTP sets
  current_price directly, so P&L/current value are accurate immediately —
  it's only CAGR/XIRR since-inception that reads as ~0 until real
  transaction history exists). New symbols get asset_class guessed via
  simple heuristics (ELSS→mf_elss, "Fund"→mf_equity, GOLD/SILVER→gold,
  else equity_large_cap) and flagged in the response for review.
  Dry-run preview before commit.
- "Import CSV" dialog on the Holdings page — file picker, preview table,
  confirm. Verified end-to-end against the user's real 25-holding export.
- 15 new tests (126 total) — CSV parser edge cases (missing columns,
  unparseable rows, blank rows) and API-level auth/validation/shape.
- Discussed Kite Connect (live sync instead of manual export) — parked:
  ₹2,000/month + GST, and access tokens expire every 24h so it's not a
  set-and-forget connection either. CSV import covers the need for free.

### Blocked / Pending
- Tradebook import (real trade history/dates) not built — only the
  Holdings snapshot format, so CAGR/XIRR on newly-imported holdings won't
  be accurate until that exists
- Edit/delete holdings and transactions still needs UI

### Next Week
- Remaining medium priority: monthly returns heatmap, rolling returns
  chart, holding detail page, tax P&L report

---

## Week 6.1 — 22 Jul 2026

### Goal
Actually run the real Zerodha import against production — found two real
bugs doing it.

### Done ✅
- **Bug 1**: `Stock.symbol` was `VARCHAR(30)` — fine for stock tickers,
  too short for mutual fund names used as a symbol fallback ("CANARA
  ROBECO ELSS TAX SAVER FUND", 34 chars). Widened to `VARCHAR(100)`
  (model + a direct `ALTER TABLE` on the live Neon table, no Alembic
  migration infra exists yet). Also hardened `commit_import()`'s
  per-row loop to catch any exception, not just `PortfolioWriteError`
  — the DB error had propagated uncaught and killed the batch mid-way,
  silently leaving 5 of 25 rows unimported with no error surfaced.
- **Bug 2**: XIRR is mathematically undefined when every cashflow lands
  on the same date (zero elapsed time) — exactly what a CSV-imported
  holding creates (bought "today", valued "today"). `pyxirr` returns
  `inf` rather than raising or returning `None`, which isn't
  JSON-serializable and 500'd the holdings endpoint the moment any
  same-day holding existed. Guarded both `calculate_xirr()` and
  `calculate_portfolio_xirr()` with `math.isfinite()`.
- Recovered the partial import cleanly: the 20 rows that succeeded
  before bug 1 crashed the batch were left alone (re-running the full
  CSV would have duplicated their transactions), only the 5 missing
  mutual funds were imported via a targeted retry.
- Production now has the real 32-holding portfolio (9 original + 23
  from the Zerodha import) fully live and verified through the API.
- 3 new regression tests (129 total): same-day XIRR for both the
  per-holding and portfolio-level functions, and a CSV-import test
  proving one row's DB error no longer aborts the rest of the batch.

### Next Week
- Remaining medium priority: monthly returns heatmap, rolling returns
  chart, holding detail page, tax P&L report

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
