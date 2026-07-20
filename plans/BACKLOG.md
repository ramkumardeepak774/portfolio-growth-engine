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
| 5 | PostgreSQL price cache | Neon DB provisioned but unused — app still hits Yahoo Finance live |
| 6 | Real portfolio growth chart | Currently using top holding as proxy — inaccurate |
| 7 | Add transaction from UI | Holdings are YAML-only right now — needs UI |
| 8 | Backend auth (`/auth/token`) | Frontend login form has nothing to call; API is fully public right now |

---

## Medium Priority

| # | Item | Why |
|---|---|---|
| 5 | CSV import (Zerodha format) | Easier to onboard real data |
| 6 | Monthly returns heatmap | Great for visualising seasonality |
| 7 | Rolling returns chart | Shows consistency over time |
| 8 | Holding detail page | Click a holding → see full history + chart |
| 9 | Tax P&L report | STCG / LTCG for filing purposes |

---

## Low Priority / Nice to Have

| # | Item | Notes |
|---|---|---|
| 10 | Watchlist | Track stocks before buying |
| 11 | SIP tracker | Are scheduled SIPs happening? |
| 12 | Dividend tracker | Log dividend income |
| 13 | MF overlap checker | Check if MFs hold the same stocks |
| 14 | Portfolio stress test | Simulate 30% market crash |
| 15 | Goal scenario planner | What if I add ₹10K/month? |

---

## Bugs / Issues

| # | Issue | Status |
|---|---|---|
| — | Portfolio growth chart uses top holding as proxy instead of real weighted value | Open |
| — | XIRR on frontend is client-side — needs actual transaction cashflows from API | Open |
