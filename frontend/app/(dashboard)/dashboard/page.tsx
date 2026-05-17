"use client"

import { useMemo } from "react"
import { Header } from "@/components/layout/header"
import { KPICard } from "@/components/dashboard/kpi-card"
import { InsightsCard } from "@/components/dashboard/insights-card"
import { PortfolioGrowthChart } from "@/components/charts/portfolio-growth-chart"
import { BenchmarkChart } from "@/components/charts/benchmark-chart"
import { SectorPieChart } from "@/components/charts/sector-pie-chart"
import { DrawdownChart } from "@/components/charts/drawdown-chart"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { usePortfolioSummary, useHoldings, useAllocation, useStockPrices } from "@/hooks/use-portfolio"
import { formatINR, formatPct, formatRatio } from "@/lib/format"
import {
  toDailyReturns,
  toDrawdownSeries,
  calcBeta,
  calcAlpha,
  calcSharpe,
  calcVolatility,
  calcMaxDrawdown,
  generateInsights,
} from "@/lib/financial"
import { DollarSign, TrendingUp, Activity, Percent } from "lucide-react"

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } = usePortfolioSummary()
  const { data: holdings, isLoading: holdingsLoading } = useHoldings()
  const { data: allocation, isLoading: allocLoading } = useAllocation()

  // Fetch NIFTY 50 as benchmark (NSE: ^NSEI)
  const { data: niftyPrices } = useStockPrices("^NSEI", "1y")
  // Use top holding for portfolio growth proxy
  const topHolding = holdings?.[0]?.symbol
  const { data: topPrices } = useStockPrices(topHolding ?? "", "1y")

  // Build comparison chart data (indexed to 100)
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

  // Build portfolio growth chart (from top holding as proxy)
  const growthData = useMemo(() => {
    if (!topPrices?.length || !summary) return []
    return topPrices.map((p) => ({
      date: p.Date.split("T")[0],
      value: summary.total_value, // approximate — real portfolio value would need weighted calc
    }))
  }, [topPrices, summary])

  // Build drawdown data
  const drawdownData = useMemo(() => {
    if (!topPrices?.length) return []
    const values = topPrices.map((p) => p.Close)
    return toDrawdownSeries(values).map((d, i) => ({
      date: topPrices[i]?.Date.split("T")[0] ?? String(i),
      drawdown: d.drawdown,
    }))
  }, [topPrices])

  // Calculate analytics
  const analytics = useMemo(() => {
    if (!topPrices?.length || !niftyPrices?.length) return null
    const pReturns = toDailyReturns(topPrices.map((p) => p.Close))
    const bReturns = toDailyReturns(niftyPrices.map((p) => p.Close))
    const vol = calcVolatility(pReturns)
    const beta = calcBeta(pReturns, bReturns)
    const cagr = summary?.cagr ?? 0
    const alpha = beta !== null ? calcAlpha(cagr, 12, beta) : null
    const sharpe = vol !== null ? calcSharpe(cagr, 6.5, vol) : null
    const maxDD = calcMaxDrawdown(topPrices.map((p) => p.Close))
    return { vol, beta, alpha, sharpe, maxDD }
  }, [topPrices, niftyPrices, summary])

  // Build sector pie data
  const sectorData = useMemo(() => {
    if (!allocation?.by_sector) return []
    return Object.entries(allocation.by_sector)
      .filter(([, v]) => v > 0)
      .map(([name, value]) => ({ name, value: Number(value.toFixed(1)) }))
      .sort((a, b) => b.value - a.value)
  }, [allocation])

  // Generate insights
  const insights = useMemo(() => {
    if (!allocation || !summary) return []
    return generateInsights({
      sectorAllocation: allocation.by_sector ?? {},
      assetClassAllocation: allocation.by_asset_class ?? {},
      beta: analytics?.beta ?? null,
      maxDrawdown: analytics?.maxDD ?? null,
      cagr: summary.cagr,
      top3Pct: allocation.concentration?.top3_pct,
    })
  }, [allocation, summary, analytics])

  const loading = summaryLoading || holdingsLoading || allocLoading

  return (
    <div className="flex flex-col">
      <Header
        title="Dashboard"
        subtitle={`${holdings?.length ?? 0} holdings · Last refreshed just now`}
      />

      <div className="p-6 space-y-6">
        {/* KPI Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
          <KPICard
            title="Portfolio Value"
            value={summary ? formatINR(summary.total_value, true) : "—"}
            trend={summary && summary.total_pnl > 0 ? "up" : "down"}
            trendLabel={summary ? formatINR(summary.total_pnl, true) + " P&L" : ""}
            icon={<DollarSign className="size-4" />}
            loading={summaryLoading}
            highlight
          />
          <KPICard
            title="Invested"
            value={summary ? formatINR(summary.total_invested, true) : "—"}
            loading={summaryLoading}
          />
          <KPICard
            title="Total Returns"
            value={summary ? formatPct(summary.total_pnl_pct) : "—"}
            trend={summary && summary.total_pnl_pct > 0 ? "up" : "down"}
            loading={summaryLoading}
          />
          <KPICard
            title="CAGR"
            value={summary ? formatPct(summary.cagr) : "—"}
            trend={summary && summary.cagr > 12 ? "up" : "neutral"}
            trendLabel="vs 12% benchmark"
            icon={<TrendingUp className="size-4" />}
            loading={summaryLoading}
          />
          <KPICard
            title="XIRR"
            value={summary?.xirr != null ? formatPct(summary.xirr) : "—"}
            trend={summary?.xirr != null && summary.xirr > 12 ? "up" : "neutral"}
            icon={<Percent className="size-4" />}
            loading={summaryLoading}
          />
          <KPICard
            title="Holdings"
            value={String(summary?.holdings_count ?? "—")}
            icon={<Activity className="size-4" />}
            loading={summaryLoading}
          />
        </div>

        {/* Analytics strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard
            title="Beta"
            value={formatRatio(analytics?.beta ?? null)}
            trend={analytics?.beta != null && analytics.beta > 1.3 ? "down" : "neutral"}
            loading={loading}
          />
          <KPICard
            title="Sharpe Ratio"
            value={formatRatio(analytics?.sharpe ?? null)}
            trend={analytics?.sharpe != null && analytics.sharpe > 1 ? "up" : "neutral"}
            loading={loading}
          />
          <KPICard
            title="Volatility"
            value={analytics?.vol != null ? formatPct(analytics.vol, 1) : "—"}
            trend={analytics?.vol != null && analytics.vol > 20 ? "down" : "neutral"}
            loading={loading}
          />
          <KPICard
            title="Max Drawdown"
            value={analytics?.maxDD != null ? formatPct(-analytics.maxDD, 1) : "—"}
            trend={analytics?.maxDD != null && analytics.maxDD > 25 ? "down" : "neutral"}
            loading={loading}
          />
        </div>

        {/* Charts row 1 */}
        <div className="grid xl:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Portfolio vs NIFTY 50</CardTitle>
            </CardHeader>
            <CardContent>
              <BenchmarkChart data={comparisonData} loading={!topPrices || !niftyPrices} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Sector Allocation</CardTitle>
            </CardHeader>
            <CardContent>
              <SectorPieChart data={sectorData} loading={allocLoading} />
            </CardContent>
          </Card>
        </div>

        {/* Charts row 2 */}
        <div className="grid xl:grid-cols-3 gap-4">
          <Card className="xl:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Drawdown</CardTitle>
            </CardHeader>
            <CardContent>
              <DrawdownChart data={drawdownData} loading={!topPrices} />
            </CardContent>
          </Card>

          <InsightsCard insights={insights} loading={loading} />
        </div>
      </div>
    </div>
  )
}
