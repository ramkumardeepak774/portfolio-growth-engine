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
