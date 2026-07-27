"use client"

import { useMemo, useState } from "react"
import { Header } from "@/components/layout/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useHoldings } from "@/hooks/use-portfolio"
import { applyStressScenario } from "@/lib/financial"
import { formatINR, formatPct, pnlColor } from "@/lib/format"
import { AlertTriangle } from "lucide-react"

const SHOCK_PRESETS = [
  { value: "-10", label: "-10%" },
  { value: "-20", label: "-20%" },
  { value: "-30", label: "-30%" },
  { value: "-40", label: "-40%" },
  { value: "-50", label: "-50%" },
]

export default function StressTestPage() {
  const { data: holdings, isLoading } = useHoldings()
  const [shockPct, setShockPct] = useState("-30")

  const rows = useMemo(() => {
    if (!holdings) return []
    return applyStressScenario(holdings, Number(shockPct))
  }, [holdings, shockPct])

  const currentTotal = rows.reduce((acc, r) => acc + r.current_value, 0)
  const stressedTotal = rows.reduce((acc, r) => acc + r.stressed_value, 0)
  const loss = stressedTotal - currentTotal
  const lossPct = currentTotal > 0 ? (loss / currentTotal) * 100 : 0

  return (
    <div className="flex flex-col">
      <Header title="Stress Test" subtitle="Simulate a market crash on your actual holdings" />

      <div className="p-6 space-y-6">
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertTriangle className="size-4 text-amber-500 mt-0.5 shrink-0" />
            <p className="text-xs text-muted-foreground">
              The shock applies to direct equity holdings only (large/mid/small/micro-cap stocks) —
              mutual funds, gold, FD/PPF/EPF/NPS, real estate, crypto, and cash are shown unaffected
              rather than guessed at. Applied uniformly across affected holdings, not adjusted for
              individual stock volatility.
            </p>
          </CardContent>
        </Card>

        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">Market Shock</span>
          <Tabs value={shockPct} onValueChange={(v) => v && setShockPct(v)}>
            <TabsList>
              {SHOCK_PRESETS.map((s) => (
                <TabsTrigger key={s.value} value={s.value}>
                  {s.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Current Portfolio Value</p>
              {isLoading ? (
                <Skeleton className="h-6 w-24 mt-1" />
              ) : (
                <p className="text-lg font-semibold mt-0.5">{formatINR(currentTotal, true)}</p>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Value After Shock</p>
              {isLoading ? (
                <Skeleton className="h-6 w-24 mt-1" />
              ) : (
                <p className="text-lg font-semibold mt-0.5">{formatINR(stressedTotal, true)}</p>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Absolute Loss</p>
              {isLoading ? (
                <Skeleton className="h-6 w-24 mt-1" />
              ) : (
                <p className={`text-lg font-semibold mt-0.5 ${pnlColor(loss)}`}>
                  {formatINR(loss, true)}
                </p>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">% Loss (Total Portfolio)</p>
              {isLoading ? (
                <Skeleton className="h-6 w-24 mt-1" />
              ) : (
                <p className={`text-lg font-semibold mt-0.5 ${pnlColor(lossPct)}`}>
                  {formatPct(lossPct)}
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Per-Holding Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-6 text-xs">Symbol</TableHead>
                  <TableHead className="text-xs">Asset Class</TableHead>
                  <TableHead className="text-xs">Current Value</TableHead>
                  <TableHead className="text-xs pr-6">Stressed Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 6 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 4 }).map((_, j) => (
                        <TableCell key={j}>
                          <Skeleton className="h-4 w-full" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-12 text-sm text-muted-foreground">
                      No holdings to stress test.
                    </TableCell>
                  </TableRow>
                ) : (
                  rows.map((r) => (
                    <TableRow key={r.symbol}>
                      <TableCell className="pl-6 text-sm font-medium">{r.symbol}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                          {r.asset_class.replace(/_/g, " ")}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">{formatINR(r.current_value, true)}</TableCell>
                      <TableCell className="pr-6 text-sm">
                        {r.affected ? (
                          <span className={pnlColor(r.stressed_value - r.current_value)}>
                            {formatINR(r.stressed_value, true)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">Unaffected</span>
                        )}
                      </TableCell>
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
