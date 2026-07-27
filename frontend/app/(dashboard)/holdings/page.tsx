"use client"

import { useState, useMemo, type ChangeEvent } from "react"
import Link from "next/link"
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
import { TransactionFields, type TransactionFieldsValue } from "@/components/holdings/transaction-fields"
import { EditHoldingForm } from "@/components/holdings/edit-holding-form"
import { DeleteHoldingConfirm } from "@/components/holdings/delete-holding-confirm"
import { useHoldings, useAddTransaction, useImportCsv } from "@/hooks/use-portfolio"
import { formatINR, formatPct, pnlColor } from "@/lib/format"
import { ASSET_CLASSES } from "@/lib/constants"
import { Plus, Search, TrendingUp, TrendingDown, Upload, Pencil, Trash2 } from "lucide-react"
import type { HoldingRow, ImportCsvResponse, TransactionType } from "@/types"

function HoldingSkeleton() {
  return (
    <TableRow>
      {Array.from({ length: 9 }).map((_, i) => (
        <TableCell key={i}>
          <Skeleton className="h-4 w-full" />
        </TableCell>
      ))}
    </TableRow>
  )
}

function HoldingRow({
  holding,
  onEdit,
  onDelete,
}: {
  holding: HoldingRow
  onEdit: () => void
  onDelete: () => void
}) {
  const positive = holding.pnl >= 0
  return (
    <TableRow className="group">
      <TableCell className="font-medium">
        <Link href={`/holdings/${encodeURIComponent(holding.symbol)}`} className="block hover:underline">
          <p className="text-sm font-semibold">{holding.symbol}</p>
          <p className="text-xs text-muted-foreground truncate max-w-[120px]">{holding.name}</p>
        </Link>
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
      <TableCell className="pr-6">
        <div className="flex items-center justify-end gap-1">
          <Button variant="ghost" size="icon" className="size-7" onClick={onEdit}>
            <Pencil className="size-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="size-7 text-red-400 hover:text-red-400"
            onClick={onDelete}
          >
            <Trash2 className="size-3.5" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  )
}

export default function HoldingsPage() {
  const { data: holdings, isLoading } = useHoldings()
  const [search, setSearch] = useState("")
  const [addOpen, setAddOpen] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [editingHolding, setEditingHolding] = useState<HoldingRow | null>(null)
  const [deletingHolding, setDeletingHolding] = useState<HoldingRow | null>(null)

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
                <Dialog open={importOpen} onOpenChange={setImportOpen}>
                  <DialogTrigger className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg border border-border bg-background px-2.5 h-8 text-xs font-medium transition-colors hover:bg-muted">
                    <Upload className="size-3.5" /> Import CSV
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Import Holdings from Zerodha</DialogTitle>
                    </DialogHeader>
                    <ImportCsvForm onClose={() => setImportOpen(false)} />
                  </DialogContent>
                </Dialog>
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
                  <TableHead className="text-xs pr-6 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 6 }).map((_, i) => <HoldingSkeleton key={i} />)
                ) : filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center py-12 text-sm text-muted-foreground">
                      {search ? "No holdings match your search." : "No holdings found. Add your first holding."}
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((h) => (
                    <HoldingRow
                      key={h.symbol}
                      holding={h}
                      onEdit={() => setEditingHolding(h)}
                      onDelete={() => setDeletingHolding(h)}
                    />
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <Dialog open={editingHolding !== null} onOpenChange={(open) => !open && setEditingHolding(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Holding</DialogTitle>
          </DialogHeader>
          {editingHolding && (
            <EditHoldingForm holding={editingHolding} onClose={() => setEditingHolding(null)} />
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={deletingHolding !== null} onOpenChange={(open) => !open && setDeletingHolding(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Hide Holding</DialogTitle>
          </DialogHeader>
          {deletingHolding && (
            <DeleteHoldingConfirm holding={deletingHolding} onClose={() => setDeletingHolding(null)} />
          )}
        </DialogContent>
      </Dialog>
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

      <TransactionFields value={form} onChange={(v) => setForm((s) => ({ ...s, ...v }))} />

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

// ── Import CSV form — Zerodha Kite "Holdings" export (Console → Portfolio
// → Holdings → Download). It's a current snapshot, not a trade history, so
// each row becomes one synthetic "buy" transaction dated today at average
// cost — CAGR/XIRR since-inception will read as ~0 until real transaction
// history exists. Preview (dry run) before committing. ──────────────────
function ImportCsvForm({ onClose }: { onClose: () => void }) {
  const { mutate, isPending, error, reset } = useImportCsv()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<ImportCsvResponse | null>(null)
  const [result, setResult] = useState<ImportCsvResponse | null>(null)

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] ?? null)
    setPreview(null)
    setResult(null)
    reset()
  }

  const handlePreview = () => {
    if (!file) return
    mutate({ file, dryRun: true }, { onSuccess: setPreview })
  }

  const handleConfirm = () => {
    if (!file) return
    mutate({ file, dryRun: false }, { onSuccess: setResult })
  }

  if (result) {
    return (
      <div className="space-y-3 mt-2">
        <p className="text-sm">
          Imported <span className="font-semibold">{result.imported_count}</span> holding
          {result.imported_count === 1 ? "" : "s"}.
        </p>
        {result.new_symbols.length > 0 && (
          <p className="text-xs text-muted-foreground">
            New holdings (asset class auto-guessed — double-check these):{" "}
            {result.new_symbols.join(", ")}
          </p>
        )}
        {result.errors.length > 0 && (
          <div className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-md space-y-1">
            {result.errors.map((e) => (
              <p key={e.symbol}>
                {e.symbol}: {e.message}
              </p>
            ))}
          </div>
        )}
        <Button className="w-full h-8 text-sm" onClick={onClose}>
          Done
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-4 mt-2">
      <p className="text-xs text-muted-foreground">
        Upload the Holdings CSV from Kite (Console → Portfolio → Holdings → Download). This is a
        current snapshot, not full trade history — each row becomes one buy transaction dated
        today at average cost, so CAGR/XIRR since inception won&apos;t be accurate until real
        transaction history exists for these holdings.
      </p>

      <Input type="file" accept=".csv" className="h-8 text-sm" onChange={handleFileChange} />

      {preview && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">
            {preview.rows.length} holding{preview.rows.length === 1 ? "" : "s"} will be imported
            {preview.new_symbols.length > 0 && ` (${preview.new_symbols.length} new)`}.
          </p>
          <div className="max-h-48 overflow-y-auto rounded-md border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-xs">Symbol</TableHead>
                  <TableHead className="text-xs">Qty</TableHead>
                  <TableHead className="text-xs">Avg Cost</TableHead>
                  <TableHead className="text-xs"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {preview.rows.map((r) => (
                  <TableRow key={r.symbol}>
                    <TableCell className="text-xs">{r.symbol}</TableCell>
                    <TableCell className="text-xs">{r.quantity}</TableCell>
                    <TableCell className="text-xs">{formatINR(r.avg_cost)}</TableCell>
                    <TableCell>
                      {r.is_new_holding && (
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                          New — {r.inferred_asset_class}
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          {preview.errors.length > 0 && (
            <div className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-md space-y-1">
              {preview.errors.map((e) => (
                <p key={e.row}>
                  Row {e.row} ({e.symbol}): {e.message}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {error && (
        <p className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-md">{error.message}</p>
      )}

      {!preview ? (
        <Button className="w-full h-8 text-sm" disabled={!file || isPending} onClick={handlePreview}>
          {isPending ? "Reading…" : "Preview"}
        </Button>
      ) : (
        <Button
          className="w-full h-8 text-sm"
          disabled={isPending || preview.rows.length === 0}
          onClick={handleConfirm}
        >
          {isPending ? "Importing…" : `Confirm Import (${preview.rows.length})`}
        </Button>
      )}
    </div>
  )
}
