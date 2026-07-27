# Backlog

> Unplanned ideas and feature requests. Prioritise from here into the roadmap.

---

## High Priority

| # | Item | Why |
|---|---|---|
| ~~1~~ | ~~Backend unit tests (pytest)~~ | Done — `tests/` (68 tests: analyzer, allocator, models, API) |
| ~~2~~ | ~~Frontend unit tests (Vitest)~~ | Done — `frontend/lib/*.test.ts` (57 tests) |
| ~~3~~ | ~~GitHub Actions CI~~ | Done — `.github/workflows/test.yml` |
| ~~4~~ | ~~Deploy to Vercel + Railway~~ | Done — see Phase 5 in ROADMAP.md for URLs |
| ~~5~~ | ~~PostgreSQL price cache~~ | Done — `src/price_cache.py`, upserts into Neon's `price_history` table |
| ~~6~~ | ~~Real portfolio growth chart~~ | Done — `portfolio_value_series()` reconstructs real weighted value; growth/drawdown/benchmark/Beta/Alpha/Sharpe/Vol all use it now |
| ~~7~~ | ~~Add transaction from UI~~ | Done — portfolio storage migrated to Postgres, `POST /api/portfolio/transactions`, Holdings page form |
| ~~8~~ | ~~Backend auth (`/auth/token`)~~ | Done — JWT via `src/auth.py`, all `/api/*` routes now gated |

---

## Medium Priority

| # | Item | Why |
|---|---|---|
| ~~5~~ | ~~CSV import (Zerodha format)~~ | Done — `POST /api/portfolio/import/csv`, Kite Holdings export, dry-run preview + confirm |
| ~~6~~ | ~~Monthly returns heatmap~~ | Done — client-side, `/analytics` |
| ~~7~~ | ~~Rolling returns chart~~ | Done — 1Y/3Y/5Y toggle, `/analytics` |
| ~~8~~ | ~~Holding detail page~~ | Done — `holdings/[symbol]`, price chart + transaction history |
| ~~9~~ | ~~Tax P&L report~~ | Done — STCG/LTCG, FIFO, equity/equity-MF only, `/tax-report` |
| ~~10~~ | ~~Edit/delete transactions~~ | Done — negative-quantity guard, `holdings/[symbol]` |
| ~~11~~ | ~~Edit/delete holdings~~ | Done — soft-delete via `is_active`, holdings list + detail page |
| 12 | Tradebook CSV import | Deferred — needs a real Zerodha Tradebook export to build against; revisit if manual re-entry becomes a real problem |

---

## Low Priority / Nice to Have

| # | Item | Notes |
|---|---|---|
| ~~10~~ | ~~Watchlist~~ | Done — `/watchlist`, live prices, target price + notes |
| 11 | SIP tracker | Are scheduled SIPs happening? |
| 12 | Dividend tracker | Log dividend income |
| 13 | MF overlap checker | Check if MFs hold the same stocks |
| 14 | Portfolio stress test | Simulate 30% market crash |
| 15 | Goal scenario planner | What if I add ₹10K/month? |

---

## Bugs / Issues

| # | Issue | Status |
|---|---|---|
| — | ~~Portfolio growth chart uses top holding as proxy instead of real weighted value~~ | Fixed — `portfolio_value_series()` |
| — | ~~XIRR on frontend is client-side~~ | Stale — `summary.xirr` already comes from the backend's real transaction-based XIRR; the unused client-side `calcXIRR` in `lib/financial.ts` is dead code, not a live bug |
| — | ~~`/api/portfolio/holdings` and `/api/data/prices/{symbol}` returned wrong field casing~~ | Fixed — broke the Holdings page, analytics page, and dashboard benchmark chart |
| — | ~~NaN close price crashes `/api/portfolio/growth`~~ | Fixed — Yahoo's still-forming intraday bar filtered out in `price_cache.py` |
