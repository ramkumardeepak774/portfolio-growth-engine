"use client"

import { useMemo } from "react"
import { Header } from "@/components/layout/header"
import { KPICard } from "@/components/dashboard/kpi-card"
import { BenchmarkChart } from "@/components/charts/benchmark-chart"
import { DrawdownChart } from "@/components/charts/drawdown-chart"
import { SectorPieChart } from "@/components/charts/sector-pie-chart"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Skeleton } from "@/components/ui/skeleton"
import { Info } from "lucide-react"
import {
  usePortfolioSummary,
  useHoldings,
  useAllocation,
  useRebalance,
  useStockPrices,
} from "@/hooks/use-portfolio"
import {
  calcBeta,
  calcAlpha,
  calcSharpe,
  calcVolatility,
  calcMaxDrawdown,
  toDailyReturns,
  toDrawdownSeries,
} from "@/lib/financial"
import { formatPct, formatRatio, formatINR, pnlColor } from "@/lib/format"

const METRICS = [
  {
    key: "cagr",
    label: "CAGR",
    desc: "Compound Annual Growth Rate — the annualised % return on your portfolio.",
  },
  {
    key: "xirr",
    label: "XIRR",
    desc: "Extended Internal Rate of Return — accounts for irregular investment timing (SIPs, lump sums).",
  },
  {
    key: "alpha",
    label: "Alpha",
    desc: "Excess return vs. market benchmark after adjusting for beta (risk). Positive = outperforming.",
  },
  {
    key: "beta",
    label: "Beta",
    desc: "Sensitivity to market movements. Beta > 1 = more volatile than market.",
  },
  {
    key: "sharpe",
    label: "Sharpe Ratio",
    desc: "Risk-adjusted return: (Portfolio Return − Risk Free Rate) / Volatility. Higher is better.",
  },
  {
    key: "volatility",
    label: "Volatility",
    desc: "Annualised standard deviation of daily returns. Measures portfolio risk.",
  },
  {
    key: "maxDD",
    label: "Max Drawdown",
    desc: "Largest peak-to-trough decline. Measures worst-case loss scenario.",
  },
]

function MetricCard({
  label,
  value,
  desc,
  trend,
  loading,
}: {
  label: string
  value: string
  desc: string
  trend?: "up" | "down" | "neutral"
  loading?: boolean
}) {
  if (loading) {
    return (
      <Card>
        <CardContent className="p-5">
          <Skeleton className="h-3 w-20 mb-3" />
          <Skeleton className="h-6 w-24 mb-2" />
          <Skeleton className="h-3 w-full" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center gap-1.5 mb-2">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            {label}
          </span>
          <Tooltip>
            <TooltipTrigger className="cursor-help inline-flex">
              <Info className="size-3 text-muted-foreground/60" />
            </TooltipTrigger>
            <TooltipContent className="max-w-[220px] text-xs">{desc}</TooltipContent>
          </Tooltip>
        </div>
        <p className="text-2xl font-semibold tracking-tight">{value}</p>
        {trend && (
          <Badge
            variant="secondary"
            className={`mt-2 text-[10px] px-1.5 py-0 ${
              trend === "up"
                ? "bg-emerald-500/10 text-emerald-500"
                : trend === "down"
                  ? "bg-red-400/10 text-red-400"
                  : ""
            }`}
          >
            {trend === "up" ? "Good" : trend === "down" ? "Monitor" : "Neutral"}
          </Badge>
        )}
      </CardContent>
    </Card>
  )
}

export default function AnalyticsPage() {
  const { data: summary, isLoading: sumLoading } = usePortfolioSummary()
  const { data: holdings } = useHoldings()
  const { data: allocation, isLoading: allocLoading } = useAllocation()
  const { data: rebalance, isLoading: rebalanceLoading } = useRebalance()

  const topHolding = holdings?.[0]?.symbol
  const { data: topPrices } = useStockPrices(topHolding ?? "", "1y")
  const { data: niftyPrices } = useStockPrices("^NSEI", "1y")

  const analytics = useMemo(() => {
    if (!topPrices?.length || !niftyPrices?.length || !summary) return null
    const pReturns = toDailyReturns(topPrices.map((p) => p.Close))
    const bReturns = toDailyReturns(niftyPrices.map((p) => p.Close))
    const vol = calcVolatility(pReturns)
    const beta = calcBeta(pReturns, bReturns)
    const cagr = summary.cagr
      const bCagr =
      niftyPrices.length > 1
        ? ((niftyPrices.at(-1)!.Close / niftyPrices[0].Close) ** (365 / niftyPrices.length) - 1) * 100
        : 12
    const alpha = beta !== null ? calcAlpha(cagr, bCagr, beta) : null
    const sharpe = vol !== null ? calcSharpe(cagr, 6.5, vol) : null
    const maxDD = calcMaxDrawdown(topPrices.map((p) => p.Close))
    return { vol, beta, alpha, sharpe, maxDD, bCagr }
  }, [topPrices, niftyPrices, summary])

  const loading = sumLoading || !topPrices || !niftyPrices

  const comparisonData = useMemo(() => {
    if (!topPrices?.length || !niftyPrices?.length) return []
    const len = Math.min(topPrices.length, niftyPrices.length)
    const base1 = topPrices[0].Close
    const base2 = niftyPrices[0].Close
    return Array.from({ length: len }, (_, i) => ({
      date: topPrices[i].Date.split("T")[0],
      portfolio: ((topPrices[i].Close - base1) / base1) * 100,
      benchmark: ((niftyPrices[i].Close - base2) / base2) * 100,
    }))
  }, [topPrices, niftyPrices])

  const drawdownData = useMemo(() => {
    if (!topPrices?.length) return []
    const values = topPrices.map((p) => p.Close)
    return toDrawdownSeries(values).map((d, i) => ({
      date: topPrices[i]?.Date.split("T")[0] ?? "",
      drawdown: d.drawdown,
    }))
  }, [topPrices])

  const sectorData = useMemo(() => {
    if (!allocation?.by_sector) return []
    return Object.entries(allocation.by_sector)
      .filter(([, v]) => v > 0)
      .map(([name, value]) => ({ name, value: Number(value.toFixed(1)) }))
      .sort((a, b) => b.value - a.value)
  }, [allocation])

  return (
    <div className="flex flex-col">
      <Header title="Analytics" subtitle="Risk & performance metrics" />

      <div className="p-6 space-y-6">
        {/* Metric cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="CAGR"
            value={summary ? formatPct(summary.cagr) : "—"}
            desc={METRICS[0].desc}
            trend={summary && summary.cagr > 12 ? "up" : "neutral"}
            loading={sumLoading}
          />
          <MetricCard
            label="XIRR"
            value={summary?.xirr != null ? formatPct(summary.xirr) : "—"}
            desc={METRICS[1].desc}
            trend={summary?.xirr != null && summary.xirr > 12 ? "up" : "neutral"}
            loading={sumLoading}
          />
          <MetricCard
            label="Alpha"
            value={analytics?.alpha != null ? formatPct(analytics.alpha, 2) : "—"}
            desc={METRICS[2].desc}
            trend={analytics?.alpha != null && analytics.alpha > 0 ? "up" : "down"}
            loading={loading}
          />
          <MetricCard
            label="Beta"
            value={formatRatio(analytics?.beta ?? null)}
            desc={METRICS[3].desc}
            trend={
              analytics?.beta != null && analytics.beta > 1.3
                ? "down"
                : analytics?.beta != null && analytics.beta < 0.8
                  ? "up"
                  : "neutral"
            }
            loading={loading}
          />
          <MetricCard
            label="Sharpe Ratio"
            value={formatRatio(analytics?.sharpe ?? null)}
            desc={METRICS[4].desc}
            trend={analytics?.sharpe != null && analytics.sharpe > 1 ? "up" : "neutral"}
            loading={loading}
          />
          <MetricCard
            label="Volatility"
            value={analytics?.vol != null ? formatPct(analytics.vol, 1) : "—"}
            desc={METRICS[5].desc}
            trend={analytics?.vol != null && analytics.vol > 25 ? "down" : "neutral"}
            loading={loading}
          />
          <MetricCard
            label="Max Drawdown"
            value={analytics?.maxDD != null ? formatPct(-analytics.maxDD, 1) : "—"}
            desc={METRICS[6].desc}
            trend={analytics?.maxDD != null && analytics.maxDD > 25 ? "down" : "neutral"}
            loading={loading}
          />
          <MetricCard
            label="Benchmark Return"
            value={analytics?.bCagr != null ? formatPct(analytics.bCagr, 1) : "—"}
            desc="NIFTY 50 annualised return for the same period."
            trend="neutral"
            loading={loading}
          />
        </div>

        {/* Charts */}
        <div className="grid xl:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Portfolio vs NIFTY 50 (1Y)</CardTitle>
            </CardHeader>
            <CardContent>
              <BenchmarkChart data={comparisonData} loading={loading} height={240} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Sector Allocation</CardTitle>
            </CardHeader>
            <CardContent>
              <SectorPieChart data={sectorData} loading={allocLoading} height={240} />
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Drawdown Chart</CardTitle>
          </CardHeader>
          <CardContent>
            <DrawdownChart data={drawdownData} loading={!topPrices} height={200} />
          </CardContent>
        </Card>

        {/* Rebalance */}
        {!rebalanceLoading && rebalance && rebalance.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Rebalancing Suggestions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {rebalance.map((r) => (
                  <div
                    key={r.bucket}
                    className="flex items-center justify-between gap-4 py-2 border-b border-border last:border-0"
                  >
                    <div>
                      <p className="text-sm font-medium capitalize">
                        {r.bucket.replace(/_/g, " ")}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Current: {r.current_pct.toFixed(1)}% → Target: {r.target_pct.toFixed(1)}%
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-medium ${pnlColor(r.diff_pct)}`}>
                        {r.diff_pct > 0 ? "+" : ""}
                        {r.diff_pct.toFixed(1)}%
                      </span>
                      <Badge
                        variant="secondary"
                        className={`text-xs ${
                          r.action === "buy"
                            ? "bg-emerald-500/10 text-emerald-500"
                            : "bg-red-400/10 text-red-400"
                        }`}
                      >
                        {r.action.toUpperCase()} {formatINR(r.amount, true)}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
