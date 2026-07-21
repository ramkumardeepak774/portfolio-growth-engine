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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useHoldings, useAddTransaction } from "@/hooks/use-portfolio"
import { formatINR, formatPct, pnlColor } from "@/lib/format"
import { Plus, Search, TrendingUp, TrendingDown } from "lucide-react"
import type { HoldingRow, TransactionType } from "@/types"

const TXN_TYPES: { value: TransactionType; label: string }[] = [
  { value: "buy", label: "Buy" },
  { value: "sell", label: "Sell" },
  { value: "sip", label: "SIP" },
  { value: "dividend", label: "Dividend" },
  { value: "switch", label: "Switch" },
]

const ASSET_CLASSES: { value: string; label: string }[] = [
  { value: "equity_large_cap", label: "Equity — Large Cap" },
  { value: "equity_mid_cap", label: "Equity — Mid Cap" },
  { value: "equity_small_cap", label: "Equity — Small Cap" },
  { value: "equity_micro_cap", label: "Equity — Micro Cap" },
  { value: "mf_equity", label: "Mutual Fund — Equity" },
  { value: "mf_hybrid", label: "Mutual Fund — Hybrid" },
  { value: "mf_debt", label: "Mutual Fund — Debt" },
  { value: "mf_index", label: "Mutual Fund — Index" },
  { value: "mf_elss", label: "Mutual Fund — ELSS" },
  { value: "gold", label: "Gold" },
  { value: "fd", label: "Fixed Deposit" },
  { value: "ppf", label: "PPF" },
  { value: "epf", label: "EPF" },
  { value: "nps", label: "NPS" },
  { value: "real_estate", label: "Real Estate" },
  { value: "crypto", label: "Crypto" },
  { value: "cash", label: "Cash" },
  { value: "other", label: "Other" },
]

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
  const [addOpen, setAddOpen] = useState(false)

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
                <Dialog open={addOpen} onOpenChange={setAddOpen}>
                  <DialogTrigger className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg bg-primary text-primary-foreground px-2.5 h-8 text-xs font-medium transition-colors hover:bg-primary/90">
                    <Plus className="size-3.5" /> Add Transaction
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add Transaction</DialogTitle>
                    </DialogHeader>
                    <AddTransactionForm onClose={() => setAddOpen(false)} />
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

// ── Add Transaction form — works for both a brand-new holding (name +
// asset_class required) and adding to an existing one (just the trade
// details; the backend looks the symbol up and tells us if it's new) ──────
function AddTransactionForm({ onClose }: { onClose: () => void }) {
  const { mutate, isPending, error } = useAddTransaction()
  const [form, setForm] = useState({
    symbol: "",
    type: "buy" as TransactionType,
    date: new Date().toISOString().slice(0, 10),
    quantity: "",
    price: "",
    charges: "",
    name: "",
    asset_class: "",
    sector: "",
  })

  const isValid = form.symbol.trim() && form.date && Number(form.quantity) > 0 && Number(form.price) > 0

  const handleSubmit = () => {
    if (!isValid) return
    mutate(
      {
        symbol: form.symbol.trim().toUpperCase(),
        type: form.type,
        date: form.date,
        quantity: Number(form.quantity),
        price: Number(form.price),
        charges: form.charges ? Number(form.charges) : 0,
        name: form.name.trim() || undefined,
        asset_class: form.asset_class || undefined,
        sector: form.sector.trim() || undefined,
      },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="space-y-4 mt-2">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="symbol" className="text-xs">
            Symbol *
          </Label>
          <Input
            id="symbol"
            className="h-8 text-sm uppercase"
            placeholder="RELIANCE"
            value={form.symbol}
            onChange={(e) => setForm((s) => ({ ...s, symbol: e.target.value.toUpperCase() }))}
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Type *</Label>
          <Select value={form.type} onValueChange={(v) => setForm((s) => ({ ...s, type: v as TransactionType }))}>
            <SelectTrigger className="h-8 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TXN_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value} className="text-sm">
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="quantity" className="text-xs">
            Quantity *
          </Label>
          <Input
            id="quantity"
            type="number"
            className="h-8 text-sm"
            placeholder="10"
            value={form.quantity}
            onChange={(e) => setForm((s) => ({ ...s, quantity: e.target.value }))}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="price" className="text-xs">
            Price (₹) *
          </Label>
          <Input
            id="price"
            type="number"
            className="h-8 text-sm"
            placeholder="2500"
            value={form.price}
            onChange={(e) => setForm((s) => ({ ...s, price: e.target.value }))}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="date" className="text-xs">
            Date *
          </Label>
          <Input
            id="date"
            type="date"
            className="h-8 text-sm"
            value={form.date}
            onChange={(e) => setForm((s) => ({ ...s, date: e.target.value }))}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="charges" className="text-xs">
            Charges (₹)
          </Label>
          <Input
            id="charges"
            type="number"
            className="h-8 text-sm"
            placeholder="0"
            value={form.charges}
            onChange={(e) => setForm((s) => ({ ...s, charges: e.target.value }))}
          />
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Only needed if <span className="font-medium">{form.symbol || "this symbol"}</span> is a new holding:
      </p>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="name" className="text-xs">
            Name
          </Label>
          <Input
            id="name"
            className="h-8 text-sm"
            placeholder="Reliance Industries"
            value={form.name}
            onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))}
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Asset Class</Label>
          <Select
            value={form.asset_class}
            onValueChange={(v) => setForm((s) => ({ ...s, asset_class: v ?? "" }))}
          >
            <SelectTrigger className="h-8 text-sm">
              <SelectValue placeholder="Select…" />
            </SelectTrigger>
            <SelectContent>
              {ASSET_CLASSES.map((a) => (
                <SelectItem key={a.value} value={a.value} className="text-sm">
                  {a.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5 col-span-2">
          <Label htmlFor="sector" className="text-xs">
            Sector
          </Label>
          <Input
            id="sector"
            className="h-8 text-sm"
            placeholder="Energy"
            value={form.sector}
            onChange={(e) => setForm((s) => ({ ...s, sector: e.target.value }))}
          />
        </div>
      </div>

      {error && (
        <p className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-md">{error.message}</p>
      )}

      <Button
        className="w-full h-8 text-sm mt-2"
        disabled={!isValid || isPending}
        onClick={handleSubmit}
      >
        {isPending ? "Saving…" : "Save Transaction"}
      </Button>
    </div>
  )
}
