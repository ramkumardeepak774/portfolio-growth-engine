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

---

## Phase 3 — Data & Analytics (Planned 📋)

- [ ] PostgreSQL integration for price caching (avoid repeated Yahoo API calls)
- [ ] Neon PostgreSQL deployment (free tier)
- [ ] Benchmark price cache (NIFTY 50, NIFTY Next 50, SENSEX)
- [ ] Historical portfolio value reconstruction from transactions
- [ ] Real portfolio growth chart (not just proxy from top holding)
- [ ] XIRR calculation from actual transaction history on frontend
- [ ] Monthly returns heatmap (calendar view)
- [ ] Rolling returns chart (1Y, 3Y, 5Y rolling CAGR)

---

## Phase 4 — Portfolio Management UI (Planned 📋)

- [ ] Add/edit/delete holdings directly from UI
- [ ] Add transactions from UI (buy, sell, SIP, dividend)
- [ ] Import transactions from CSV (Zerodha, Groww format)
- [ ] Holdings sorted by various columns
- [ ] Holding detail page (full transaction history, price chart, fundamentals)
- [ ] SIP tracker — are your SIPs on schedule?

---

## Phase 5 — Deployment (Planned 📋)

- [ ] Deploy frontend to Vercel
- [ ] Deploy backend to Railway / Render
- [ ] Setup Neon PostgreSQL
- [ ] Environment variables configured on Vercel
- [ ] CORS updated for production URL
- [ ] Custom domain (optional)

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
