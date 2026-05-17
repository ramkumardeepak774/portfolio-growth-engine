# Portfolio Growth Engine — Frontend

A modern, professional portfolio analytics dashboard built with **Next.js 16**, **TypeScript**, **Tailwind CSS v4**, and **shadcn/ui**. Connects to the existing **FastAPI** backend.

---

## Features

| Feature | Details |
|---|---|
| **Dashboard** | Portfolio value, invested, total returns, CAGR, XIRR, beta, Sharpe, volatility, max drawdown |
| **Benchmark Comparison** | Portfolio vs NIFTY 50 indexed growth chart |
| **Holdings** | Full holdings table with P&L, sector badges, search |
| **Analytics** | Alpha, beta, Sharpe, volatility, max drawdown, rebalancing suggestions |
| **Decision Journal** | Document reasoning before every trade, review outcomes |
| **Settings** | API URL configuration, theme toggle (dark/light/system) |

---

## Tech Stack

- **Framework** — Next.js 16 (App Router)
- **Language** — TypeScript (strict, zero errors)
- **Styling** — Tailwind CSS v4 + shadcn/ui (Base UI)
- **Charts** — Recharts
- **Data fetching** — TanStack Query v5 (5-min stale time)
- **HTTP** — Axios with JWT Bearer interceptors
- **Theme** — next-themes (dark by default)
- **Hosting** — Vercel (free tier)

---

## Quick Start

### 1. Install

```bash
cd frontend
npm install
```

### 2. Configure environment

```bash
cp .env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_AUTH_DISABLED=true   ← local dev shortcut
```

### 3. Start FastAPI backend

```bash
# project root
uvicorn src.app:app --reload --port 8000
```

### 4. Start frontend

```bash
npm run dev          # http://localhost:3000
```

---

## Project Structure

```
frontend/
├── app/
│   ├── (auth)/login/         Login page (JWT + demo mode)
│   ├── (dashboard)/          Auth-guarded layout + sidebar
│   │   ├── dashboard/        KPIs, charts, insights
│   │   ├── holdings/         Holdings table + search
│   │   ├── analytics/        Risk metrics + rebalancing
│   │   ├── journal/          Decision journal
│   │   └── settings/         API URL + theme
│   └── globals.css           Finance-themed colour palette
├── components/
│   ├── charts/               Recharts wrappers (growth, benchmark, pie, drawdown)
│   ├── dashboard/            KPI cards, insights card
│   ├── layout/               Sidebar, header
│   └── ui/                   shadcn/ui components
├── contexts/auth-context.tsx JWT auth state
├── hooks/                    TanStack Query hooks
├── lib/
│   ├── api.ts                Axios client + interceptors
│   ├── financial.ts          CAGR, XIRR, Alpha, Beta, Sharpe, Volatility, Drawdown
│   └── format.ts             INR formatting, % formatting
├── services/                 Typed API service layer
└── types/index.ts            All TypeScript interfaces
```

---

## Financial Calculations (lib/financial.ts)

| Metric | Formula |
|---|---|
| CAGR | `(FV/PV)^(1/n) − 1` |
| XIRR | Newton-Raphson on irregular cashflows |
| Volatility | Annualised std dev × √252 |
| Max Drawdown | Peak-to-trough decline |
| Beta | Cov(P, B) / Var(B) |
| Alpha | `Return − (Rf + β × (Rm − Rf))` |
| Sharpe | `(Return − 6.5%) / Volatility` |

---

## API Endpoints Used

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/portfolio/summary` | Dashboard KPIs |
| GET | `/api/portfolio/holdings` | Holdings table |
| GET | `/api/portfolio/allocation` | Sector/asset allocation |
| GET | `/api/portfolio/rebalance` | Rebalancing suggestions |
| GET | `/api/data/prices/{symbol}` | Price charts & analytics |
| GET | `/api/journal/entries` | Journal list |
| POST | `/api/journal/entry` | Create entry |

---

## Deployment

### Frontend → Vercel

1. Push `frontend/` to GitHub
2. Import on [vercel.com](https://vercel.com)
3. Add env var: `NEXT_PUBLIC_API_URL=https://your-api.railway.app`

### Backend → Railway / Render / Fly.io (free tiers)

Update CORS in `src/app.py`:
```python
allow_origins=["https://your-app.vercel.app"]
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI backend URL |
| `NEXT_PUBLIC_AUTH_DISABLED` | `false` | Skip login (dev only, never in prod) |

---

## Cost

| Service | Cost |
|---|---|
| Vercel (frontend) | ₹0 |
| Railway/Render (backend) | ₹0 free tier |
| **Total** | **₹0/month** |
