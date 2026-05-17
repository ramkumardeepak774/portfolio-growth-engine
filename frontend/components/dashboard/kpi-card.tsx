import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import type { ReactNode } from "react"

interface KPICardProps {
  title: string
  value: string
  subValue?: string
  trend?: "up" | "down" | "neutral"
  trendLabel?: string
  icon?: ReactNode
  loading?: boolean
  highlight?: boolean
}

export function KPICard({
  title,
  value,
  subValue,
  trend,
  trendLabel,
  icon,
  loading,
  highlight,
}: KPICardProps) {
  if (loading) {
    return (
      <Card className="relative overflow-hidden">
        <CardContent className="p-5">
          <Skeleton className="h-3 w-24 mb-3" />
          <Skeleton className="h-7 w-32 mb-2" />
          <Skeleton className="h-3 w-20" />
        </CardContent>
      </Card>
    )
  }

  const TrendIcon =
    trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus

  const trendColor =
    trend === "up"
      ? "text-emerald-500"
      : trend === "down"
        ? "text-red-400"
        : "text-muted-foreground"

  return (
    <Card
      className={cn(
        "relative overflow-hidden transition-shadow hover:shadow-md",
        highlight && "border-primary/30 bg-primary/5",
      )}
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-1">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            {title}
          </p>
          {icon && (
            <span className="text-muted-foreground/60">{icon}</span>
          )}
        </div>
        <p className="text-2xl font-semibold tracking-tight mt-1">{value}</p>
        {(subValue || trendLabel) && (
          <div className={cn("flex items-center gap-1 mt-1.5 text-xs", trendColor)}>
            {trend && <TrendIcon className="size-3" />}
            <span>{subValue ?? trendLabel}</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
