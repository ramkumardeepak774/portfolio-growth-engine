"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { AlertTriangle, Info, CheckCircle2 } from "lucide-react"
import type { Insight } from "@/types"
import { cn } from "@/lib/utils"

interface InsightsCardProps {
  insights: Insight[]
  loading?: boolean
}

const iconMap = {
  warning: AlertTriangle,
  info: Info,
  success: CheckCircle2,
}

const colorMap = {
  warning: "text-amber-500 bg-amber-500/10",
  info: "text-blue-400 bg-blue-400/10",
  success: "text-emerald-500 bg-emerald-500/10",
}

export function InsightsCard({ insights, loading }: InsightsCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold">Portfolio Insights</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex gap-3">
              <Skeleton className="size-8 rounded-lg shrink-0" />
              <div className="space-y-1.5 flex-1">
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-3 w-full" />
              </div>
            </div>
          ))
        ) : insights.length === 0 ? (
          <p className="text-sm text-muted-foreground py-2">No insights available yet.</p>
        ) : (
          insights.map((insight, i) => {
            const Icon = iconMap[insight.type]
            return (
              <div key={i} className="flex gap-3 items-start">
                <div
                  className={cn(
                    "flex items-center justify-center size-8 rounded-lg shrink-0",
                    colorMap[insight.type],
                  )}
                >
                  <Icon className="size-4" />
                </div>
                <div>
                  <p className="text-xs font-medium">{insight.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{insight.description}</p>
                </div>
              </div>
            )
          })
        )}
      </CardContent>
    </Card>
  )
}
