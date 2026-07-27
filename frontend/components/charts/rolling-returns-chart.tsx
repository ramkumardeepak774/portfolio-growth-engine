"use client"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts"
import { format, parseISO } from "date-fns"
import { Skeleton } from "@/components/ui/skeleton"
import type { RollingReturnPoint } from "@/lib/financial"

interface RollingReturnsChartProps {
  data: RollingReturnPoint[]
  loading?: boolean
  height?: number
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{ value: number | null }>
  label?: string
}) {
  if (!active || !payload?.length || payload[0].value === null) return null
  return (
    <div className="rounded-lg border border-border bg-popover p-3 shadow-lg text-xs">
      <p className="text-muted-foreground mb-1">
        {label ? format(parseISO(label), "dd MMM yyyy") : ""}
      </p>
      <p className="font-medium text-foreground">{payload[0].value!.toFixed(2)}%</p>
    </div>
  )
}

export function RollingReturnsChart({ data, loading, height = 220 }: RollingReturnsChartProps) {
  if (loading) return <Skeleton style={{ height }} className="w-full rounded-lg" />

  const plottable = data.filter((d) => d.rolling_cagr_pct !== null)
  if (!plottable.length) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center text-sm text-muted-foreground"
      >
        Not enough history yet for a rolling window
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
        <XAxis
          dataKey="date"
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          tickFormatter={(v) => {
            try {
              return format(parseISO(v), "MMM yy")
            } catch {
              return v
            }
          }}
          interval="preserveStartEnd"
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          tickFormatter={(v) => `${v > 0 ? "+" : ""}${v.toFixed(0)}%`}
          width={50}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={0} stroke="hsl(var(--border))" />
        <Line
          type="monotone"
          dataKey="rolling_cagr_pct"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          dot={false}
          connectNulls={false}
          activeDot={{ r: 4, strokeWidth: 0 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
