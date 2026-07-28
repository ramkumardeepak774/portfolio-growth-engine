"use client"

import { useMemo, useState } from "react"
import { Header } from "@/components/layout/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useDividendSummary } from "@/hooks/use-portfolio"
import { formatINR } from "@/lib/format"
import { currentFyOption, fyOptions } from "@/lib/fy"
import { Info } from "lucide-react"

function formatMonth(monthKey: string): string {
  const [year, month] = monthKey.split("-").map(Number)
  return new Date(year, month - 1).toLocaleDateString("en-IN", { month: "short", year: "numeric" })
}

export default function DividendsPage() {
  const [fy, setFy] = useState(currentFyOption())
  const { data: summary, isLoading } = useDividendSummary(fy)
  const options = useMemo(fyOptions, [])

  return (
    <div className="flex flex-col">
      <Header title="Dividends" subtitle="Dividend income by financial year" />

      <div className="p-6 space-y-6">
        <Card className="border-border bg-muted/30">
          <CardContent className="p-4 flex items-start gap-3">
            <Info className="size-4 text-muted-foreground mt-0.5 shrink-0" />
            <p className="text-xs text-muted-foreground">
              Dividend income is taxed as &ldquo;income from other sources&rdquo; at your slab rate —
              a different tax head from the Tax Report&apos;s capital gains, not part of it.
            </p>
          </CardContent>
        </Card>

        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">Financial Year</span>
          <Select value={fy} onValueChange={(v) => v && setFy(v)}>
            <SelectTrigger className="h-8 w-32 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {options.map((o) => (
                <SelectItem key={o} value={o} className="text-sm">
                  FY {o}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Total Dividend Income</p>
            {isLoading ? (
              <Skeleton className="h-6 w-24 mt-1" />
            ) : (
              <p className="text-lg font-semibold mt-0.5 text-emerald-500">
                {formatINR(summary?.total_dividend_income ?? 0, true)}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">By Holding</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-6 text-xs">Symbol</TableHead>
                  <TableHead className="text-xs">Name</TableHead>
                  <TableHead className="text-xs">Payments</TableHead>
                  <TableHead className="text-xs pr-6">Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 4 }).map((_, j) => (
                        <TableCell key={j}>
                          <Skeleton className="h-4 w-full" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : !summary?.by_holding.length ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-10 text-sm text-muted-foreground">
                      No dividends recorded for this financial year.
                    </TableCell>
                  </TableRow>
                ) : (
                  summary.by_holding.map((h) => (
                    <TableRow key={h.symbol}>
                      <TableCell className="pl-6 text-sm font-medium">{h.symbol}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{h.name}</TableCell>
                      <TableCell className="text-sm">{h.count}</TableCell>
                      <TableCell className="pr-6 text-sm font-medium text-emerald-500">
                        {formatINR(h.total)}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">By Month</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-6 text-xs">Month</TableHead>
                  <TableHead className="text-xs pr-6">Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell>
                        <Skeleton className="h-4 w-full" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-4 w-full" />
                      </TableCell>
                    </TableRow>
                  ))
                ) : !summary?.by_month.length ? (
                  <TableRow>
                    <TableCell colSpan={2} className="text-center py-10 text-sm text-muted-foreground">
                      No dividends recorded for this financial year.
                    </TableCell>
                  </TableRow>
                ) : (
                  summary.by_month.map((m) => (
                    <TableRow key={m.month}>
                      <TableCell className="pl-6 text-sm">{formatMonth(m.month)}</TableCell>
                      <TableCell className="pr-6 text-sm font-medium text-emerald-500">
                        {formatINR(m.total)}
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
