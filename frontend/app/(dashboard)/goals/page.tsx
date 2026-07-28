"use client"

import { useMemo, useState } from "react"
import { Header } from "@/components/layout/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useGoals } from "@/hooks/use-portfolio"
import { goalMilestones, projectGoalValue } from "@/lib/financial"
import { formatINR, formatPct, pnlColor } from "@/lib/format"
import { Target } from "lucide-react"

const CAGR_PRESETS = ["12", "15", "20", "25", "30", "35", "40", "50"]

export default function GoalsPage() {
  const { data: goals, isLoading } = useGoals()
  const [selectedName, setSelectedName] = useState<string | null>(null)
  const [cagrInput, setCagrInput] = useState("20")
  const [yearsInput, setYearsInput] = useState("")

  const selected = useMemo(() => {
    if (!goals?.length) return null
    return goals.find((g) => g.name === selectedName) ?? goals[0]
  }, [goals, selectedName])

  const cagrPct = Number(cagrInput) || 0
  const years = yearsInput === "" ? (selected?.years_remaining ?? 0) : Number(yearsInput) || 0

  const projected = selected ? projectGoalValue(selected.current_value, cagrPct, years) : 0
  const willHitTarget = selected ? projected >= selected.target_value : false
  const milestones = selected ? goalMilestones(selected.current_value, cagrPct, years) : []

  return (
    <div className="flex flex-col">
      <Header title="Goals" subtitle="Long-term wealth targets and what-if scenarios" />

      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="p-4 space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-6 w-24" />
                  <Skeleton className="h-4 w-40" />
                </CardContent>
              </Card>
            ))
          ) : !goals?.length ? (
            <Card className="md:col-span-3">
              <CardContent className="p-8 text-center text-sm text-muted-foreground">
                No goals configured.
              </CardContent>
            </Card>
          ) : (
            goals.map((g) => (
              <Card key={g.name}>
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-semibold">{g.name}</p>
                    <Badge variant={g.on_track ? "default" : "destructive"} className="text-[10px] px-1.5 py-0">
                      {g.on_track ? "On Track" : "Off Track"}
                    </Badge>
                  </div>
                  <p className="text-lg font-semibold">{formatINR(g.current_value, true)}</p>
                  <p className="text-xs text-muted-foreground">
                    Target {formatINR(g.target_value, true)} · {g.target_multiplier}x in {g.target_years}y
                  </p>
                  <div className="grid grid-cols-2 gap-2 pt-1 text-xs">
                    <div>
                      <p className="text-muted-foreground">Actual CAGR</p>
                      <p className={pnlColor(g.actual_cagr)}>{formatPct(g.actual_cagr)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Required CAGR</p>
                      <p>{formatPct(g.required_cagr)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Years Remaining</p>
                      <p>{g.years_remaining.toFixed(1)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Completion</p>
                      <p>{g.completion_pct.toFixed(1)}%</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {!isLoading && Boolean(goals?.length) && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Target className="size-4" />
                Scenario Planner
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap items-center gap-6">
                <div className="flex items-center gap-3">
                  <span className="text-sm text-muted-foreground">Goal</span>
                  <Select
                    value={selected?.name}
                    onValueChange={(v) => {
                      if (v) {
                        setSelectedName(v)
                        setYearsInput("")
                      }
                    }}
                  >
                    <SelectTrigger className="h-8 w-56 text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {goals!.map((g) => (
                        <SelectItem key={g.name} value={g.name} className="text-sm">
                          {g.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-sm text-muted-foreground">Years</span>
                  <Input
                    type="number"
                    className="h-8 w-20"
                    value={yearsInput}
                    placeholder={selected?.years_remaining.toFixed(1)}
                    onChange={(e) => setYearsInput(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">Assumed CAGR</span>
                <Tabs value={cagrInput} onValueChange={(v) => v && setCagrInput(v)}>
                  <TabsList>
                    {CAGR_PRESETS.map((r) => (
                      <TabsTrigger key={r} value={r}>
                        {r}%
                      </TabsTrigger>
                    ))}
                  </TabsList>
                </Tabs>
                <Input
                  type="number"
                  className="h-8 w-20"
                  value={cagrInput}
                  onChange={(e) => setCagrInput(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-2">
                <div>
                  <p className="text-xs text-muted-foreground">Projected Corpus</p>
                  <p className="text-lg font-semibold">{formatINR(projected, true)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Target Corpus</p>
                  <p className="text-lg font-semibold">{formatINR(selected?.target_value ?? 0, true)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Outcome</p>
                  <Badge variant={willHitTarget ? "default" : "destructive"} className="text-[10px] px-1.5 py-0">
                    {willHitTarget ? "Target Reached" : "Target Missed"}
                  </Badge>
                </div>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground pt-2 pb-1">Milestones</p>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="pl-0 text-xs">Year</TableHead>
                      <TableHead className="text-xs">Projected Value</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {milestones.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={2} className="text-center py-8 text-sm text-muted-foreground">
                          No milestones for a zero-year horizon.
                        </TableCell>
                      </TableRow>
                    ) : (
                      milestones.map((m) => (
                        <TableRow key={m.year}>
                          <TableCell className="pl-0 text-sm">{m.year}</TableCell>
                          <TableCell className="text-sm">{formatINR(m.projectedValue, true)}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
