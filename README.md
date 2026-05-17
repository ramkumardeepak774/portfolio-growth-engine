# Portfolio Growth Engine 🚀

A long-term investment research, analysis, and portfolio optimization system
built for the Indian market (stocks + mutual funds).

## Goal

Grow portfolio **1000x over 20 years** → requires ~41.4% CAGR.

This is an extremely ambitious target. The system helps you get as close as
possible through disciplined research, diversification, and compounding.

## Features

| Module | What it does |
|---|---|
| **Portfolio Tracker** | Track all holdings — stocks, mutual funds, gold, FDs, etc. |
| **Analyzer** | CAGR, XIRR, drawdown, Sharpe ratio, sector concentration |
| **Goal Tracker** | Are you on track for 1000x? Shows required vs actual CAGR |
| **Asset Allocator** | Suggests rebalancing across asset classes |
| **Screener** | Research stocks/MFs using financial metrics |
| **Reporter** | Generate portfolio health reports |

## Quick Start

```bash
cd portfolio-growth-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Edit your holdings
vim data/portfolio.yaml

# Run analysis
python -m src.cli summary
python -m src.cli goal
python -m src.cli rebalance
python -m src.cli screen --type stock
python -m src.cli report
```

## Portfolio Data

Edit `data/portfolio.yaml` with your actual holdings. Example structure is
provided. All amounts are in INR.

## Key Concepts

- **CAGR**: Compound Annual Growth Rate — the annualized return
- **XIRR**: Extended IRR — accurate return when you invest at irregular intervals (SIPs)
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Max Drawdown**: Largest peak-to-trough drop (lower is better)
- **Asset Allocation**: How your money is split across stocks, MFs, debt, gold, etc.

## 20-Year Growth Math

| Multiplier | CAGR Needed | Difficulty |
|---|---|---|
| 10x | 12.2% | Achievable with index funds |
| 100x | 25.9% | Needs concentrated bets + skill |
| 1000x | 41.4% | Requires exceptional stock picking + compounding |

The 1000x target is aspirational. The system will help you maximize returns
while managing risk through proper allocation and research.

## Project Structure

```
portfolio-growth-engine/
├── data/
│   ├── portfolio.yaml       # Your holdings
│   └── goals.yaml           # Financial goals
├── src/
│   ├── models.py            # Data models
│   ├── portfolio.py         # Portfolio loading & management
│   ├── analyzer.py          # Performance analysis
│   ├── allocator.py         # Asset allocation & rebalancing
│   ├── goal_tracker.py      # Goal progress tracking
│   ├── screener.py          # Stock/MF screening
│   ├── reports.py           # Report generation
│   ├── market_data.py       # Fetch live prices
│   └── cli.py               # Command-line interface
├── notebooks/
│   └── portfolio_analysis.ipynb
├── requirements.txt
└── README.md
```
