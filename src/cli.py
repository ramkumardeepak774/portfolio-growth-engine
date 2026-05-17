"""CLI interface for Portfolio Growth Engine."""

from __future__ import annotations

import logging
import sys

import click
from rich.console import Console

from .market_data import update_portfolio_prices
from .portfolio import load_portfolio
from .reports import (
    print_allocation,
    print_goal_progress,
    print_growth_scenarios,
    print_holdings_table,
    print_portfolio_summary,
    print_rebalance,
    generate_text_report,
)
from .screener import (
    MULTI_BAGGER_THEMES,
    NIFTY_50_POPULAR,
    SMALL_CAP_WATCHLIST,
    screen_multiple,
)

console = Console()
logging.basicConfig(level=logging.WARNING)


@click.group()
def cli():
    """Portfolio Growth Engine — Research, Analyze, Grow 1000x."""
    pass


@cli.command()
@click.option("--live/--no-live", default=False, help="Fetch live prices from market")
def summary(live: bool):
    """Show portfolio summary with P&L and key metrics."""
    portfolio = load_portfolio()
    if live:
        console.print("[dim]Fetching live prices...[/dim]")
        count = update_portfolio_prices(portfolio)
        console.print(f"[dim]Updated {count} holdings[/dim]")
    print_portfolio_summary(portfolio)
    print_holdings_table(portfolio)


@cli.command()
@click.option("--live/--no-live", default=False, help="Fetch live prices")
def allocation(live: bool):
    """Show asset class and sector allocation breakdown."""
    portfolio = load_portfolio()
    if live:
        update_portfolio_prices(portfolio)
    print_allocation(portfolio)


@cli.command()
@click.option("--live/--no-live", default=False, help="Fetch live prices")
def goal(live: bool):
    """Track progress toward your 1000x goal."""
    portfolio = load_portfolio()
    if live:
        update_portfolio_prices(portfolio)
    print_goal_progress(portfolio)
    if portfolio.total_invested > 0:
        print_growth_scenarios(portfolio.total_invested)


@cli.command()
@click.option("--live/--no-live", default=False, help="Fetch live prices")
def rebalance(live: bool):
    """Get rebalancing suggestions based on target allocation."""
    portfolio = load_portfolio()
    if live:
        update_portfolio_prices(portfolio)
    print_rebalance(portfolio)


@cli.command()
@click.option("--symbols", "-s", help="Comma-separated stock symbols (e.g., RELIANCE,TCS,INFY)")
@click.option("--watchlist", "-w", type=click.Choice(["nifty50", "smallcap", "all"]), help="Pre-built watchlist")
@click.option("--theme", "-t", help=f"Theme: {', '.join(MULTI_BAGGER_THEMES.keys())}")
def screen(symbols: str | None, watchlist: str | None, theme: str | None):
    """Screen stocks for multi-bagger potential."""
    stock_list = []

    if symbols:
        stock_list = [s.strip().upper() for s in symbols.split(",")]
    elif watchlist == "nifty50":
        stock_list = NIFTY_50_POPULAR
    elif watchlist == "smallcap":
        stock_list = SMALL_CAP_WATCHLIST
    elif watchlist == "all":
        stock_list = NIFTY_50_POPULAR + SMALL_CAP_WATCHLIST
    elif theme and theme in MULTI_BAGGER_THEMES:
        stock_list = MULTI_BAGGER_THEMES[theme]
    else:
        console.print("[yellow]Specify --symbols, --watchlist, or --theme[/yellow]")
        console.print(f"Themes: {', '.join(MULTI_BAGGER_THEMES.keys())}")
        return

    console.print(f"[dim]Screening {len(stock_list)} stocks...[/dim]")
    results = screen_multiple(stock_list)

    from rich.table import Table

    table = Table(title=f"Stock Screener — {len(results)} results", show_lines=True)
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Symbol")
    table.add_column("Name")
    table.add_column("Sector")
    table.add_column("Price", justify="right")
    table.add_column("PE", justify="right")
    table.add_column("ROE %", justify="right")
    table.add_column("D/E", justify="right")
    table.add_column("Rev Gr %", justify="right")
    table.add_column("Prof Gr %", justify="right")
    table.add_column("Mkt Cap (Cr)", justify="right")

    for s in results:
        score_color = "green" if s.score >= 60 else ("yellow" if s.score >= 40 else "red")
        table.add_row(
            f"[{score_color}]{s.score}[/{score_color}]",
            s.symbol,
            s.name[:20],
            s.sector[:15],
            f"₹{s.price:,.0f}",
            f"{s.pe_ratio:.1f}",
            f"{s.roe:.1f}",
            f"{s.debt_to_equity:.1f}",
            f"{s.revenue_growth:.1f}",
            f"{s.profit_growth:.1f}",
            f"{s.market_cap:,.0f}",
        )

    console.print(table)


@cli.command()
@click.option("--live/--no-live", default=False, help="Fetch live prices")
def report(live: bool):
    """Generate a full portfolio report and save to file."""
    portfolio = load_portfolio()
    if live:
        console.print("[dim]Fetching live prices...[/dim]")
        update_portfolio_prices(portfolio)
    generate_text_report(portfolio)


@cli.command()
@click.argument("amount", type=float)
def sip(amount: float):
    """Show how to split a monthly SIP amount across buckets.

    Example: python -m src.cli sip 50000
    """
    from .allocator import suggest_monthly_sip_allocation, AGGRESSIVE_GROWTH
    from rich.table import Table

    alloc = suggest_monthly_sip_allocation(amount)
    table = Table(title=f"Monthly SIP Allocation — ₹{amount:,.0f}")
    table.add_column("Bucket")
    table.add_column("Target %", justify="right")
    table.add_column("Monthly Amount", justify="right")

    for bucket, amt in sorted(alloc.items(), key=lambda x: -x[1]):
        pct = AGGRESSIVE_GROWTH.get(bucket, 0)
        table.add_row(bucket, f"{pct}%", f"₹{amt:,.0f}")

    console.print(table)


# =====================================================================
# Layer 3 — Portfolio Risk
# =====================================================================

@cli.command()
def risk():
    """Show portfolio risk dashboard with warnings."""
    from .decisions import generate_risk_report
    from rich.table import Table
    from rich.panel import Panel

    portfolio = load_portfolio()
    report = generate_risk_report(portfolio)

    console.print(Panel.fit("[bold red]Portfolio Risk Dashboard[/bold red]", border_style="red"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Total Value", f"₹{report.total_value:,.0f}")
    table.add_row("Top 5 Concentration", f"{report.top5_concentration_pct}%")
    table.add_row("Max Sector Weight", f"{report.sector_max_pct}%")
    table.add_row("Largest Position", f"{report.largest_position_pct}%")
    table.add_row("Avg Conviction", f"{report.avg_conviction}/5")
    table.add_row("Positions w/o Thesis", str(report.positions_without_thesis))
    table.add_row("Positions w/o Stop-Loss", str(report.positions_without_stop_loss))
    console.print(table)
    console.print()

    if report.warnings:
        for w in report.warnings:
            color = "red" if "CRITICAL" in w else ("yellow" if "WARNING" in w else "cyan")
            console.print(f"  [{color}]⚠ {w}[/{color}]")
    else:
        console.print("  [green]✓ No risk warnings[/green]")


# =====================================================================
# Layer 4 — Decision Journal
# =====================================================================

@cli.command()
@click.argument("symbol")
@click.option("--action", "-a", type=click.Choice(["entry", "exit", "add", "trim", "hold", "watchlist"]), required=True)
@click.option("--why", "-w", required=True, help="Why are you making this decision?")
@click.option("--thesis", "-t", default="", help="Investment thesis")
@click.option("--conviction", "-c", type=click.Choice(["very_high", "high", "medium", "low", "speculative"]), default="medium")
@click.option("--price", "-p", type=float, default=0, help="Trade price")
@click.option("--qty", "-q", type=float, default=0, help="Quantity")
def journal(symbol: str, action: str, why: str, thesis: str, conviction: str, price: float, qty: float):
    """Log a decision in your investment journal.

    Example: python -m src.cli journal DIXON -a entry -w "Strong PLI beneficiary" -c high
    """
    from .journal import create_entry

    entry = create_entry(
        symbol=symbol.upper(),
        action=action,
        why=why,
        thesis=thesis,
        conviction=conviction,
        price=price,
        quantity=qty,
    )
    console.print(f"[green]✓ Journal entry created: {entry.id}[/green]")


@cli.command("journal-list")
@click.option("--symbol", "-s", default=None)
@click.option("--unreviewed", is_flag=True, help="Show only unreviewed entries")
def journal_list(symbol: str | None, unreviewed: bool):
    """List decision journal entries."""
    from .journal import list_entries, get_unreviewed_entries
    from rich.table import Table

    entries = get_unreviewed_entries() if unreviewed else list_entries(symbol=symbol)

    table = Table(title="Decision Journal", show_lines=True)
    table.add_column("ID")
    table.add_column("Symbol")
    table.add_column("Action")
    table.add_column("Date")
    table.add_column("Conviction")
    table.add_column("Reviewed")
    table.add_column("Rating")

    for e in entries:
        reviewed = "[green]✓[/green]" if e.is_reviewed else "[red]✗[/red]"
        table.add_row(e.id, e.symbol, e.action, e.date, e.conviction, reviewed, str(e.rating) if e.rating else "—")

    console.print(table)
    if not entries:
        console.print("[dim]No journal entries yet. Use 'journal' command to add one.[/dim]")


@cli.command()
def checklist():
    """Show pre-investment decision checklist."""
    from .journal import get_checklist

    console.print()
    console.print("[bold cyan]Pre-Investment Checklist[/bold cyan]")
    console.print()
    for item in get_checklist("entry"):
        console.print(f"  {item}")
    console.print()
    console.print("[dim]Answer ALL questions before investing. No shortcuts.[/dim]")


@cli.command("bias-report")
def bias_report():
    """Analyze your decision journal for biases and patterns."""
    from .journal import get_bias_report
    from rich.panel import Panel

    report = get_bias_report()

    console.print(Panel.fit("[bold]Decision Quality Report[/bold]", border_style="magenta"))

    if "message" in report:
        console.print(f"[yellow]{report['message']}[/yellow]")
        return

    console.print(f"  Total Reviewed Decisions: {report['total_reviewed']}")
    console.print(f"  Avg Decision Rating: {report['avg_overall_rating']}/10")
    console.print()

    if report.get("common_biases"):
        console.print("[bold]Common Biases:[/bold]")
        for bias, count in report["common_biases"].items():
            console.print(f"  • {bias}: {count} times")
    console.print()

    if report.get("avg_rating_by_conviction"):
        console.print("[bold]Rating by Conviction:[/bold]")
        for conv, rating in report["avg_rating_by_conviction"].items():
            console.print(f"  {conv}: {rating}/10")


# =====================================================================
# Server
# =====================================================================

@cli.command()
@click.option("--port", "-p", default=8000, help="Port to run on")
def serve(port: int):
    """Start the FastAPI server."""
    import uvicorn
    console.print(f"[green]Starting server on http://localhost:{port}[/green]")
    console.print("[dim]API docs: http://localhost:{port}/docs[/dim]")
    uvicorn.run("src.app:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    cli()
