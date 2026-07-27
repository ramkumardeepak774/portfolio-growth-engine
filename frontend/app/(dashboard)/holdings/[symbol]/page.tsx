"use client"

import { useMemo } from "react"
import { useParams, useRouter } from "next/navigation"
import { Header } from "@/components/layout/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { PortfolioGrowthChart } from "@/components/charts/portfolio-growth-chart"
import { useHoldingDetail, useStockPrices } from "@/hooks/use-portfolio"
import { formatINR, formatPct, formatDate, pnlColor } from "@/lib/format"
import { ArrowLeft } from "lucide-react"

const TXN_TYPE_LABELS: Record<string, string> = {
  buy: "Buy",
  sell: "Sell",
  sip: "SIP",
  dividend: "Dividend",
  switch: "Switch",
}

export default function HoldingDetailPage() {
  const params = useParams<{ symbol: string }>()
  const symbol = decodeURIComponent(params.symbol ?? "")
  const router = useRouter()

  const { data: holding, isLoading, isError } = useHoldingDetail(symbol)
  const { data: prices, isLoading: pricesLoading } = useStockPrices(symbol, "1y")

  const priceChartData = useMemo(() => {
    if (!prices?.length) return []
    return prices.map((p) => ({ date: p.Date.split("T")[0], value: p.Close }))
  }, [prices])

  if (isError) {
    return (
      <div className="flex flex-col">
        <Header title="Holding not found" />
        <div className="p-6">
          <Card>
            <CardContent className="p-8 text-center space-y-3">
              <p className="text-sm text-muted-foreground">
                No active holding for symbol &ldquo;{symbol}&rdquo;.
              </p>
              <Button variant="outline" size="sm" onClick={() => router.push("/holdings")}>
                <ArrowLeft className="size-3.5 mr-1.5" /> Back to Holdings
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col">
      <Header
        title={isLoading ? "Loading…" : holding?.symbol ?? symbol}
        subtitle={holding?.name}
      />

      <div className="p-6 space-y-6">
        <Button variant="ghost" size="sm" className="w-fit -ml-2" onClick={() => router.push("/holdings")}>
          <ArrowLeft className="size-3.5 mr-1.5" /> Back to Holdings
        </Button>

        {/* KPI strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Quantity", value: isLoading ? null : holding?.quantity.toLocaleString("en-IN") },
            { label: "Invested", value: isLoading ? null : formatINR(holding?.invested_amount ?? 0, true) },
            { label: "Current Value", value: isLoading ? null : formatINR(holding?.current_value ?? 0, true) },
            {
              label: "P&L",
              value: isLoading ? null : formatINR(holding?.pnl ?? 0, true),
              pct: holding?.pnl_percent,
            },
          ].map((kpi) => (
            <Card key={kpi.label}>
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground">{kpi.label}</p>
                {kpi.value === null ? (
                  <Skeleton className="h-6 w-20 mt-1" />
                ) : (
                  <p className={`text-lg font-semibold mt-0.5 ${kpi.pct !== undefined ? pnlColor(kpi.pct) : ""}`}>
                    {kpi.value}
                    {kpi.pct !== undefined && (
                      <span className="text-xs font-normal ml-1.5">({formatPct(kpi.pct)})</span>
                    )}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {holding && (
          <div className="flex items-center gap-2">
            {holding.sector && <Badge variant="secondary">{holding.sector}</Badge>}
            <Badge variant="outline">{holding.asset_class.replace(/_/g, " ")}</Badge>
          </div>
        )}

        {/* Price chart */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Price History (1Y)</CardTitle>
          </CardHeader>
          <CardContent>
            <PortfolioGrowthChart data={priceChartData} loading={pricesLoading} height={240} />
          </CardContent>
        </Card>

        {/* Transaction history */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Transaction History</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-6 text-xs">Date</TableHead>
                  <TableHead className="text-xs">Type</TableHead>
                  <TableHead className="text-xs">Quantity</TableHead>
                  <TableHead className="text-xs">Price</TableHead>
                  <TableHead className="text-xs">Charges</TableHead>
                  <TableHead className="text-xs">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 6 }).map((_, j) => (
                        <TableCell key={j}>
                          <Skeleton className="h-4 w-full" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : !holding?.transactions.length ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-12 text-sm text-muted-foreground">
                      No transactions recorded for this holding.
                    </TableCell>
                  </TableRow>
                ) : (
                  holding.transactions.map((t, i) => (
                    <TableRow key={t.id ?? i}>
                      <TableCell className="pl-6 text-sm">{formatDate(t.date)}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                          {TXN_TYPE_LABELS[t.type] ?? t.type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">{t.quantity.toLocaleString("en-IN")}</TableCell>
                      <TableCell className="text-sm">{formatINR(t.price)}</TableCell>
                      <TableCell className="text-sm">{formatINR(t.charges)}</TableCell>
                      <TableCell className="text-sm font-medium">{formatINR(t.amount)}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
