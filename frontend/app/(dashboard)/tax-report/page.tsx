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
import { useTaxReport } from "@/hooks/use-portfolio"
import { formatINR, formatDate, pnlColor } from "@/lib/format"
import { currentFyOption, fyOptions } from "@/lib/fy"
import { AlertTriangle } from "lucide-react"

function GainTable({ title, gain, lots, loading }: { title: string; gain: number; lots: { symbol: string; buy_date: string; sell_date: string; quantity: number; buy_price: number; sell_price: number; gain: number }[]; loading: boolean }) {
  return (
    <Card>
      <CardHeader className="pb-2 flex-row items-center justify-between">
        <CardTitle className="text-sm font-semibold">{title}</CardTitle>
        {!loading && (
          <span className={`text-sm font-semibold ${pnlColor(gain)}`}>{formatINR(gain, true)}</span>
        )}
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="pl-6 text-xs">Symbol</TableHead>
              <TableHead className="text-xs">Buy Date</TableHead>
              <TableHead className="text-xs">Sell Date</TableHead>
              <TableHead className="text-xs">Qty</TableHead>
              <TableHead className="text-xs">Buy Price</TableHead>
              <TableHead className="text-xs">Sell Price</TableHead>
              <TableHead className="text-xs">Gain</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 7 }).map((_, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : lots.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-10 text-sm text-muted-foreground">
                  No {title.toLowerCase()} lots for this financial year.
                </TableCell>
              </TableRow>
            ) : (
              lots.map((lot, i) => (
                <TableRow key={i}>
                  <TableCell className="pl-6 text-sm font-medium">{lot.symbol}</TableCell>
                  <TableCell className="text-sm">{formatDate(lot.buy_date)}</TableCell>
                  <TableCell className="text-sm">{formatDate(lot.sell_date)}</TableCell>
                  <TableCell className="text-sm">{lot.quantity.toLocaleString("en-IN")}</TableCell>
                  <TableCell className="text-sm">{formatINR(lot.buy_price)}</TableCell>
                  <TableCell className="text-sm">{formatINR(lot.sell_price)}</TableCell>
                  <TableCell className={`text-sm font-medium ${pnlColor(lot.gain)}`}>
                    {formatINR(lot.gain)}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

export default function TaxReportPage() {
  const [fy, setFy] = useState(currentFyOption())
  const { data: report, isLoading } = useTaxReport(fy)
  const options = useMemo(fyOptions, [])

  return (
    <div className="flex flex-col">
      <Header title="Tax Report" subtitle="Capital gains — STCG / LTCG" />

      <div className="p-6 space-y-6">
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertTriangle className="size-4 text-amber-500 mt-0.5 shrink-0" />
            <p className="text-xs text-muted-foreground">
              For informational purposes only — consult a qualified tax advisor before filing.
              Covers equity and equity mutual fund holdings only (FIFO lot matching, 12-month
              long-term threshold). Does not include an estimated tax payable, Section 112A
              grandfathering for pre-2018 buys, or dividend income.
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

        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Short-Term Capital Gains</p>
              {isLoading ? (
                <Skeleton className="h-6 w-24 mt-1" />
              ) : (
                <p className={`text-lg font-semibold mt-0.5 ${pnlColor(report?.stcg.total_gain ?? 0)}`}>
                  {formatINR(report?.stcg.total_gain ?? 0, true)}
                </p>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Long-Term Capital Gains</p>
              {isLoading ? (
                <Skeleton className="h-6 w-24 mt-1" />
              ) : (
                <p className={`text-lg font-semibold mt-0.5 ${pnlColor(report?.ltcg.total_gain ?? 0)}`}>
                  {formatINR(report?.ltcg.total_gain ?? 0, true)}
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        <GainTable title="Short-Term Gains" gain={report?.stcg.total_gain ?? 0} lots={report?.stcg.lots ?? []} loading={isLoading} />
        <GainTable title="Long-Term Gains" gain={report?.ltcg.total_gain ?? 0} lots={report?.ltcg.lots ?? []} loading={isLoading} />

        {!isLoading && report && report.unsupported_asset_classes.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Not Yet Supported</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {report.unsupported_asset_classes.map((u) => (
                <div key={u.asset_class} className="text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">{u.asset_class.replace(/_/g, " ")}</span>
                  {": "}
                  {u.symbols.join(", ")} — {u.note}
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
