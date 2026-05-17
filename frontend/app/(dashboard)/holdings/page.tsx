"use client"

import { useState, useMemo } from "react"
import { Header } from "@/components/layout/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { useHoldings } from "@/hooks/use-portfolio"
import { formatINR, formatPct, pnlColor } from "@/lib/format"
import { Plus, Search, TrendingUp, TrendingDown } from "lucide-react"
import type { HoldingRow } from "@/types"

function HoldingSkeleton() {
  return (
    <TableRow>
      {Array.from({ length: 8 }).map((_, i) => (
        <TableCell key={i}>
          <Skeleton className="h-4 w-full" />
        </TableCell>
      ))}
    </TableRow>
  )
}

function HoldingRow({ holding }: { holding: HoldingRow }) {
  const positive = holding.pnl >= 0
  return (
    <TableRow className="group">
      <TableCell className="font-medium">
        <div>
          <p className="text-sm font-semibold">{holding.symbol}</p>
          <p className="text-xs text-muted-foreground truncate max-w-[120px]">{holding.name}</p>
        </div>
      </TableCell>
      <TableCell className="text-sm">{holding.quantity.toLocaleString("en-IN")}</TableCell>
      <TableCell className="text-sm">
        {holding.current_price ? formatINR(holding.current_price) : "—"}
      </TableCell>
      <TableCell className="text-sm">{formatINR(holding.invested_amount, true)}</TableCell>
      <TableCell className="text-sm font-medium">{formatINR(holding.current_value, true)}</TableCell>
      <TableCell>
        <div className="flex items-center gap-1">
          {positive ? (
            <TrendingUp className="size-3 text-emerald-500" />
          ) : (
            <TrendingDown className="size-3 text-red-400" />
          )}
          <span className={`text-sm font-medium ${pnlColor(holding.pnl)}`}>
            {formatINR(holding.pnl, true)}
          </span>
        </div>
      </TableCell>
      <TableCell>
        <span className={`text-sm font-medium ${pnlColor(holding.pnl_percent)}`}>
          {formatPct(holding.pnl_percent)}
        </span>
      </TableCell>
      <TableCell>
        {holding.sector ? (
          <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
            {holding.sector}
          </Badge>
        ) : (
          <span className="text-xs text-muted-foreground">—</span>
        )}
      </TableCell>
    </TableRow>
  )
}

export default function HoldingsPage() {
  const { data: holdings, isLoading } = useHoldings()
  const [search, setSearch] = useState("")

  const filtered = useMemo(() => {
    if (!holdings) return []
    const q = search.toLowerCase()
    return holdings.filter(
      (h) =>
        h.symbol.toLowerCase().includes(q) ||
        h.name?.toLowerCase().includes(q) ||
        h.sector?.toLowerCase().includes(q),
    )
  }, [holdings, search])

  const totalValue = useMemo(
    () => filtered.reduce((acc, h) => acc + h.current_value, 0),
    [filtered],
  )

  return (
    <div className="flex flex-col">
      <Header
        title="Holdings"
        subtitle={`${holdings?.length ?? 0} positions`}
      />

      <div className="p-6 space-y-4">
        {/* Summary strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            {
              label: "Total Value",
              value: formatINR(totalValue, true),
            },
            {
              label: "Winners",
              value: String(filtered.filter((h) => h.pnl > 0).length),
            },
            {
              label: "Losers",
              value: String(filtered.filter((h) => h.pnl < 0).length),
            },
            {
              label: "Sectors",
              value: String(new Set(filtered.map((h) => h.sector).filter(Boolean)).size),
            },
          ].map((s) => (
            <Card key={s.label}>
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground">{s.label}</p>
                <p className="text-lg font-semibold mt-0.5">{s.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <CardTitle className="text-sm font-semibold">All Holdings</CardTitle>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
                  <Input
                    placeholder="Search symbol or sector…"
                    className="pl-8 h-8 w-56 text-xs"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
                <Dialog>
                  <DialogTrigger className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg bg-primary text-primary-foreground px-2.5 h-8 text-xs font-medium transition-colors hover:bg-primary/90">
                    <Plus className="size-3.5" /> Add Holding
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add Holding</DialogTitle>
                    </DialogHeader>
                    <AddHoldingForm />
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-6 text-xs">Symbol</TableHead>
                  <TableHead className="text-xs">Qty</TableHead>
                  <TableHead className="text-xs">CMP</TableHead>
                  <TableHead className="text-xs">Invested</TableHead>
                  <TableHead className="text-xs">Current Value</TableHead>
                  <TableHead className="text-xs">P&amp;L</TableHead>
                  <TableHead className="text-xs">P&amp;L %</TableHead>
                  <TableHead className="text-xs">Sector</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 6 }).map((_, i) => <HoldingSkeleton key={i} />)
                ) : filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-12 text-sm text-muted-foreground">
                      {search ? "No holdings match your search." : "No holdings found. Add your first holding."}
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((h) => <HoldingRow key={h.symbol} holding={h} />)
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// ── Add Holding form (inline — connects to backend YAML via data folder) ──────
function AddHoldingForm() {
  return (
    <div className="space-y-4 mt-2">
      <p className="text-sm text-muted-foreground">
        Holdings are managed via <code className="text-xs bg-muted px-1 rounded">data/portfolio.yaml</code>.
        Use the transaction journal below to record buys and sells.
      </p>
      <div className="grid grid-cols-2 gap-3">
        {[
          { id: "symbol", label: "Symbol" },
          { id: "qty", label: "Quantity" },
          { id: "price", label: "Buy Price (₹)" },
          { id: "date", label: "Transaction Date" },
          { id: "sector", label: "Sector" },
          { id: "asset_class", label: "Asset Class" },
        ].map((f) => (
          <div key={f.id} className="space-y-1.5">
            <Label htmlFor={f.id} className="text-xs">
              {f.label}
            </Label>
            <Input
              id={f.id}
              className="h-8 text-sm"
              placeholder={f.label}
            />
          </div>
        ))}
      </div>
      <Button className="w-full h-8 text-sm mt-2">Save Holding</Button>
    </div>
  )
}
