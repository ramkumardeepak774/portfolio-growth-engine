"use client"

import { Skeleton } from "@/components/ui/skeleton"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import type { MonthlyReturn } from "@/lib/financial"

interface MonthlyReturnsHeatmapProps {
  data: MonthlyReturn[]
  loading?: boolean
  height?: number
}

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

/** Diverging green/red intensity scale, graduated by magnitude — matches the
 * emerald/red opacity conventions already used for P&L badges elsewhere. */
function cellClasses(returnPct: number): string {
  const abs = Math.abs(returnPct)
  const bucket = abs >= 10 ? 3 : abs >= 5 ? 2 : abs >= 2 ? 1 : 0
  if (returnPct > 0) {
    return ["bg-emerald-500/10 text-emerald-600", "bg-emerald-500/20 text-emerald-600", "bg-emerald-500/30 text-emerald-500", "bg-emerald-500/40 text-emerald-500"][bucket]
  }
  if (returnPct < 0) {
    return ["bg-red-400/10 text-red-500", "bg-red-400/20 text-red-500", "bg-red-400/30 text-red-400", "bg-red-400/40 text-red-400"][bucket]
  }
  return "bg-muted/40 text-muted-foreground"
}

/** Compound monthly returns into a year total: product(1 + r/100) - 1 */
function yearTotal(returns: number[]): number {
  return (returns.reduce((acc, r) => acc * (1 + r / 100), 1) - 1) * 100
}

export function MonthlyReturnsHeatmap({ data, loading, height = 220 }: MonthlyReturnsHeatmapProps) {
  if (loading) return <Skeleton style={{ height }} className="w-full rounded-lg" />

  if (!data.length) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center text-sm text-muted-foreground"
      >
        No returns data yet
      </div>
    )
  }

  const byYear = new Map<number, Map<number, number>>()
  for (const point of data) {
    if (!byYear.has(point.year)) byYear.set(point.year, new Map())
    byYear.get(point.year)!.set(point.month, point.return_pct)
  }
  const years = Array.from(byYear.keys()).sort((a, b) => b - a)

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-separate" style={{ borderSpacing: 4 }}>
        <thead>
          <tr>
            <th className="text-xs font-medium text-muted-foreground text-left pr-2">Year</th>
            {MONTH_LABELS.map((m) => (
              <th key={m} className="text-xs font-medium text-muted-foreground text-center w-14">
                {m}
              </th>
            ))}
            <th className="text-xs font-medium text-muted-foreground text-center w-16">Year</th>
          </tr>
        </thead>
        <tbody>
          {years.map((year) => {
            const monthMap = byYear.get(year)!
            const monthValues = Array.from(monthMap.values())
            return (
              <tr key={year}>
                <td className="text-xs font-medium pr-2">{year}</td>
                {MONTH_LABELS.map((_, idx) => {
                  const month = idx + 1
                  const value = monthMap.get(month)
                  if (value === undefined) {
                    return <td key={month} className="h-9 rounded-md bg-muted/20" />
                  }
                  return (
                    <td key={month} className="p-0">
                      <Tooltip>
                        <TooltipTrigger className="w-full">
                          <div
                            className={`h-9 rounded-md flex items-center justify-center text-[11px] font-medium ${cellClasses(value)}`}
                          >
                            {value.toFixed(1)}%
                          </div>
                        </TooltipTrigger>
                        <TooltipContent className="text-xs">
                          {MONTH_LABELS[idx]} {year}: {value > 0 ? "+" : ""}
                          {value.toFixed(2)}%
                        </TooltipContent>
                      </Tooltip>
                    </td>
                  )
                })}
                <td className="text-center text-xs font-semibold">
                  {monthValues.length > 0 ? `${yearTotal(monthValues).toFixed(1)}%` : "—"}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
