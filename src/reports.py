"""Portfolio report generation."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .allocator import (
    AGGRESSIVE_GROWTH,
    calculate_rebalance,
    get_current_allocation,
    suggest_monthly_sip_allocation,
)
from .analyzer import (
    asset_class_allocation,
    calculate_portfolio_cagr,
    calculate_portfolio_xirr,
    concentration_risk,
    holding_performance_table,
    sector_allocation,
)
from .goal_tracker import GoalProgress, growth_scenarios, milestone_table, track_all_goals
from .models import Portfolio

console = Console()

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def _fmt_inr(amount: float) -> str:
    """Format amount in Indian style: ₹12,34,567."""
    if amount < 0:
        return f"-₹{_fmt_inr_abs(-amount)}"
    return f"₹{_fmt_inr_abs(amount)}"


def _fmt_inr_abs(amount: float) -> str:
    s = f"{amount:,.0f}"
    # Convert international format to Indian
    parts = s.split(",")
    if len(parts) <= 2:
        return s
    last = parts[-1]
    rest = ",".join(parts[:-1])
    # Re-group rest in pairs from right
    rest_digits = rest.replace(",", "")
    indian_parts = []
    while len(rest_digits) > 2:
        indian_parts.insert(0, rest_digits[-2:])
        rest_digits = rest_digits[:-2]
    if rest_digits:
        indian_parts.insert(0, rest_digits)
    return ",".join(indian_parts) + "," + last


def print_portfolio_summary(portfolio: Portfolio) -> None:
    """Print a rich summary of the portfolio."""
    console.print()
    console.print(Panel.fit(
        f"[bold green]Portfolio Summary[/bold green]  •  {date.today().isoformat()}",
        border_style="green",
    ))

    total_inv = portfolio.total_invested
    total_cur = portfolio.total_current_value
    pnl = portfolio.total_pnl
    pnl_pct = portfolio.total_pnl_percent
    cagr = calculate_portfolio_cagr(portfolio)
    xirr_val = calculate_portfolio_xirr(portfolio)

    pnl_color = "green" if pnl >= 0 else "red"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Total Invested", _fmt_inr(total_inv))
    table.add_row("Current Value", f"[bold]{_fmt_inr(total_cur)}[/bold]")
    table.add_row("P&L", f"[{pnl_color}]{_fmt_inr(pnl)} ({pnl_pct:+.1f}%)[/{pnl_color}]")
    table.add_row("CAGR", f"{cagr:.1f}%")
    table.add_row("XIRR", f"{xirr_val:.1f}%" if xirr_val else "N/A")
    table.add_row("Holdings", str(len(portfolio.holdings)))
    console.print(table)
    console.print()


def print_holdings_table(portfolio: Portfolio) -> None:
    """Print per-holding performance table."""
    df = holding_performance_table(portfolio)
    if df.empty:
        console.print("[yellow]No holdings found.[/yellow]")
        return

    table = Table(title="Holdings Performance", show_lines=True)
    for col in df.columns:
        justify = "right" if col not in ("Symbol", "Name", "Asset Class", "Sector") else "left"
        table.add_column(col, justify=justify)

    for _, row in df.iterrows():
        values = []
        for col in df.columns:
            val = row[col]
            if col == "P&L (₹)":
                color = "green" if val >= 0 else "red"
                values.append(f"[{color}]{_fmt_inr(val)}[/{color}]")
            elif col in ("Invested (₹)", "Current (₹)"):
                values.append(_fmt_inr(val))
            elif col in ("P&L %", "CAGR %"):
                color = "green" if val >= 0 else "red"
                values.append(f"[{color}]{val:+.1f}%[/{color}]" if isinstance(val, (int, float)) else str(val))
            else:
                values.append(str(val))
        table.add_row(*values)

    console.print(table)
    console.print()


def print_allocation(portfolio: Portfolio) -> None:
    """Print asset class and sector allocation."""
    console.print(Panel.fit("[bold]Asset Allocation[/bold]", border_style="blue"))

    ac_alloc = asset_class_allocation(portfolio)
    table = Table(title="By Asset Class")
    table.add_column("Asset Class")
    table.add_column("Value", justify="right")
    table.add_column("%", justify="right")
    table.add_column("Holdings", justify="right")
    for key, data in ac_alloc.items():
        table.add_row(data["label"], _fmt_inr(data["value"]), f"{data['percent']}%", str(data["count"]))
    console.print(table)
    console.print()

    sec_alloc = sector_allocation(portfolio)
    table = Table(title="By Sector")
    table.add_column("Sector")
    table.add_column("Value", justify="right")
    table.add_column("%", justify="right")
    for sector, data in sec_alloc.items():
        table.add_row(sector, _fmt_inr(data["value"]), f"{data['percent']}%")
    console.print(table)
    console.print()

    # Concentration risk
    conc = concentration_risk(portfolio)
    if conc["top_holdings"]:
        console.print(f"[bold yellow]Top 5 concentration: {conc['top_percent']}%[/bold yellow]")
        for h in conc["top_holdings"]:
            console.print(f"  {h['symbol']}: {_fmt_inr(h['value'])} ({h['percent']}%)")
    console.print()


def print_rebalance(portfolio: Portfolio) -> None:
    """Print rebalancing suggestions."""
    console.print(Panel.fit("[bold]Rebalance Suggestions[/bold] (Target: Aggressive Growth)", border_style="magenta"))

    actions = calculate_rebalance(portfolio)
    table = Table(show_lines=True)
    table.add_column("Bucket")
    table.add_column("Current %", justify="right")
    table.add_column("Target %", justify="right")
    table.add_column("Diff", justify="right")
    table.add_column("Action")
    table.add_column("Amount", justify="right")

    for a in actions:
        color = "green" if a.action == "BUY MORE" else ("red" if a.action == "REDUCE" else "white")
        table.add_row(
            a.bucket,
            f"{a.current_percent}%",
            f"{a.target_percent}%",
            f"[{color}]{a.diff_percent:+.1f}%[/{color}]",
            f"[{color}]{a.action}[/{color}]",
            _fmt_inr(a.amount),
        )

    console.print(table)
    console.print()


def print_goal_progress(portfolio: Portfolio) -> None:
    """Print goal tracking dashboard."""
    goals = track_all_goals(portfolio)
    if not goals:
        console.print("[yellow]No goals defined. Edit data/goals.yaml[/yellow]")
        return

    for gp in goals:
        status_color = "green" if gp.on_track else "red"
        status = "ON TRACK" if gp.on_track else "BEHIND"

        console.print(Panel.fit(
            f"[bold]{gp.goal.name}[/bold]  •  [{status_color}]{status}[/{status_color}]",
            border_style=status_color,
        ))

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold")
        table.add_column()
        table.add_row("Target", f"{gp.goal.target_multiplier:.0f}x in {gp.goal.target_years} years")
        table.add_row("Initial Corpus", _fmt_inr(gp.goal.initial_corpus))
        table.add_row("Target Value", _fmt_inr(gp.target_value))
        table.add_row("Current Value", _fmt_inr(gp.current_value))
        table.add_row("Years Elapsed", f"{gp.years_elapsed}")
        table.add_row("Years Remaining", f"{gp.years_remaining}")
        table.add_row("Required CAGR", f"{gp.required_cagr}%")
        table.add_row("Required CAGR (from now)", f"{gp.required_cagr_from_now}%")
        table.add_row("Actual CAGR", f"{gp.actual_cagr}%")
        table.add_row("Projected at Target Date", _fmt_inr(gp.projected_value_at_target))
        table.add_row("Completion", f"{gp.completion_percent}% (log scale)")
        console.print(table)
        console.print()

        # Milestone checkpoints
        milestones = milestone_table(gp.goal)
        mt = Table(title="Milestone Checkpoints")
        mt.add_column("Year")
        mt.add_column("Date")
        mt.add_column("Multiplier", justify="right")
        mt.add_column("Projected Value", justify="right")
        for m in milestones:
            if m["year"] % 5 == 0 or m["year"] <= 3:
                mt.add_row(
                    str(m["year"]),
                    str(m["date"]),
                    f"{m['multiplier']}x",
                    _fmt_inr(m["projected_value"]),
                )
        console.print(mt)
        console.print()


def print_growth_scenarios(initial_corpus: float) -> None:
    """Print growth scenario table."""
    console.print(Panel.fit("[bold]Growth Scenarios[/bold] (20-year projection)", border_style="cyan"))

    scenarios = growth_scenarios(initial_corpus)
    table = Table()
    table.add_column("CAGR %", justify="right")
    table.add_column("Final Value", justify="right")
    table.add_column("Multiplier", justify="right")
    for s in scenarios:
        table.add_row(
            f"{s['cagr_percent']}%",
            _fmt_inr(s["final_value"]),
            f"{s['multiplier']}x",
        )
    console.print(table)
    console.print()


def generate_text_report(portfolio: Portfolio, output_path: Path | None = None) -> Path:
    """Generate a full text report and save to file."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = REPORTS_DIR / f"report_{timestamp}.txt"

    from io import StringIO
    from rich.console import Console as StrConsole

    buf = StringIO()
    str_console = StrConsole(file=buf, width=120, force_terminal=True)

    # Capture all output
    original = globals()["console"]
    globals()["console"] = str_console

    print_portfolio_summary(portfolio)
    print_holdings_table(portfolio)
    print_allocation(portfolio)
    print_rebalance(portfolio)
    print_goal_progress(portfolio)
    if portfolio.total_invested > 0:
        print_growth_scenarios(portfolio.total_invested)

    globals()["console"] = original

    output_path.write_text(buf.getvalue())
    console.print(f"[green]Report saved to {output_path}[/green]")
    return output_path
