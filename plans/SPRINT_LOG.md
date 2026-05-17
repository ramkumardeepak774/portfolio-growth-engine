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
