"use client"

import { useState, useMemo } from "react"
import { Header } from "@/components/layout/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useWatchlist, useAddToWatchlist, useRemoveFromWatchlist } from "@/hooks/use-watchlist"
import { formatINR, formatPct, pnlColor } from "@/lib/format"
import { ASSET_CLASSES } from "@/lib/constants"
import { Plus, Search, Star, Trash2 } from "lucide-react"
import type { WatchlistItem } from "@/types"

function WatchlistSkeleton() {
  return (
    <TableRow>
      {Array.from({ length: 6 }).map((_, i) => (
        <TableCell key={i}>
          <Skeleton className="h-4 w-full" />
        </TableCell>
      ))}
    </TableRow>
  )
}

function distanceToTargetPct(current: number | null, target: number | null): number | null {
  if (current === null || target === null || target === 0) return null
  return ((current - target) / target) * 100
}

function WatchlistRow({ item, onRemove }: { item: WatchlistItem; onRemove: () => void }) {
  const distance = distanceToTargetPct(item.current_price, item.target_price)
  return (
    <TableRow className="group">
      <TableCell className="font-medium">
        <p className="text-sm font-semibold">{item.symbol}</p>
        <p className="text-xs text-muted-foreground truncate max-w-[160px]">{item.name}</p>
      </TableCell>
      <TableCell className="text-sm">
        {item.current_price !== null ? formatINR(item.current_price) : "—"}
      </TableCell>
      <TableCell className="text-sm">
        {item.target_price !== null ? formatINR(item.target_price) : "—"}
      </TableCell>
      <TableCell>
        {distance !== null ? (
          <span className={`text-sm font-medium ${pnlColor(-distance)}`}>{formatPct(distance)}</span>
        ) : (
          <span className="text-xs text-muted-foreground">—</span>
        )}
      </TableCell>
      <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">
        {item.notes || "—"}
      </TableCell>
      <TableCell className="pr-6">
        <div className="flex items-center justify-end">
          <Button
            variant="ghost"
            size="icon"
            className="size-7 text-red-400 hover:text-red-400"
            onClick={onRemove}
          >
            <Trash2 className="size-3.5" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  )
}

export default function WatchlistPage() {
  const { data: watchlist, isLoading } = useWatchlist()
  const [search, setSearch] = useState("")
  const [addOpen, setAddOpen] = useState(false)
  const [removingItem, setRemovingItem] = useState<WatchlistItem | null>(null)

  const filtered = useMemo(() => {
    if (!watchlist) return []
    const q = search.toLowerCase()
    return watchlist.filter(
      (w) => w.symbol.toLowerCase().includes(q) || w.name?.toLowerCase().includes(q),
    )
  }, [watchlist, search])

  return (
    <div className="flex flex-col">
      <Header title="Watchlist" subtitle={`${watchlist?.length ?? 0} symbols tracked`} />

      <div className="p-6 space-y-4">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <CardTitle className="text-sm font-semibold">Tracked Symbols</CardTitle>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
                  <Input
                    placeholder="Search symbol…"
                    className="pl-8 h-8 w-56 text-xs"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
                <Dialog open={addOpen} onOpenChange={setAddOpen}>
                  <DialogTrigger className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg bg-primary text-primary-foreground px-2.5 h-8 text-xs font-medium transition-colors hover:bg-primary/90">
                    <Plus className="size-3.5" /> Add to Watchlist
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add to Watchlist</DialogTitle>
                    </DialogHeader>
                    <AddWatchlistForm onClose={() => setAddOpen(false)} />
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
                  <TableHead className="text-xs">Current Price</TableHead>
                  <TableHead className="text-xs">Target Price</TableHead>
                  <TableHead className="text-xs">vs Target</TableHead>
                  <TableHead className="text-xs">Notes</TableHead>
                  <TableHead className="text-xs pr-6 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 4 }).map((_, i) => <WatchlistSkeleton key={i} />)
                ) : filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-12 text-sm text-muted-foreground">
                      {search ? (
                        "No watchlist symbols match your search."
                      ) : (
                        <span className="flex flex-col items-center gap-2">
                          <Star className="size-5 text-muted-foreground/50" />
                          Nothing on your watchlist yet. Add a symbol you&apos;re considering buying.
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((item) => (
                    <WatchlistRow key={item.symbol} item={item} onRemove={() => setRemovingItem(item)} />
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <Dialog open={removingItem !== null} onOpenChange={(open) => !open && setRemovingItem(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove from Watchlist</DialogTitle>
          </DialogHeader>
          {removingItem && (
            <RemoveWatchlistConfirm item={removingItem} onClose={() => setRemovingItem(null)} />
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

function AddWatchlistForm({ onClose }: { onClose: () => void }) {
  const { mutate, isPending, error } = useAddToWatchlist()
  const [form, setForm] = useState({
    symbol: "",
    name: "",
    asset_class: "",
    sector: "",
    target_price: "",
    notes: "",
  })

  const isValid = form.symbol.trim().length > 0

  const handleSubmit = () => {
    if (!isValid) return
    mutate(
      {
        symbol: form.symbol.trim().toUpperCase(),
        name: form.name.trim() || undefined,
        asset_class: form.asset_class || undefined,
        sector: form.sector.trim() || undefined,
        target_price: form.target_price ? Number(form.target_price) : undefined,
        notes: form.notes.trim() || undefined,
      },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="space-y-4 mt-2">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="wl-symbol" className="text-xs">
            Symbol *
          </Label>
          <Input
            id="wl-symbol"
            className="h-8 text-sm uppercase"
            placeholder="RELIANCE"
            value={form.symbol}
            onChange={(e) => setForm((s) => ({ ...s, symbol: e.target.value.toUpperCase() }))}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="wl-target" className="text-xs">
            Target Price (₹)
          </Label>
          <Input
            id="wl-target"
            type="number"
            className="h-8 text-sm"
            placeholder="2500"
            value={form.target_price}
            onChange={(e) => setForm((s) => ({ ...s, target_price: e.target.value }))}
          />
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Only needed if <span className="font-medium">{form.symbol || "this symbol"}</span> isn&apos;t
        already tracked:
      </p>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="wl-name" className="text-xs">
            Name
          </Label>
          <Input
            id="wl-name"
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
          <Label htmlFor="wl-sector" className="text-xs">
            Sector
          </Label>
          <Input
            id="wl-sector"
            className="h-8 text-sm"
            placeholder="Energy"
            value={form.sector}
            onChange={(e) => setForm((s) => ({ ...s, sector: e.target.value }))}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="wl-notes" className="text-xs">
          Notes
        </Label>
        <Input
          id="wl-notes"
          className="h-8 text-sm"
          placeholder="Why you're watching this…"
          value={form.notes}
          onChange={(e) => setForm((s) => ({ ...s, notes: e.target.value }))}
        />
      </div>

      {error && (
        <p className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-md">{error.message}</p>
      )}

      <Button className="w-full h-8 text-sm mt-2" disabled={!isValid || isPending} onClick={handleSubmit}>
        {isPending ? "Saving…" : "Add to Watchlist"}
      </Button>
    </div>
  )
}

function RemoveWatchlistConfirm({ item, onClose }: { item: WatchlistItem; onClose: () => void }) {
  const { mutate, isPending, error } = useRemoveFromWatchlist()

  const handleRemove = () => {
    mutate(item.symbol, { onSuccess: onClose })
  }

  return (
    <div className="space-y-4 mt-2">
      <p className="text-sm text-muted-foreground">
        Remove <span className="font-medium text-foreground">{item.symbol}</span> from your
        watchlist?
      </p>

      {error && (
        <p className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-md">{error.message}</p>
      )}

      <div className="flex gap-2">
        <Button variant="outline" className="flex-1 h-8 text-sm" onClick={onClose}>
          Cancel
        </Button>
        <Button
          variant="destructive"
          className="flex-1 h-8 text-sm"
          disabled={isPending}
          onClick={handleRemove}
        >
          {isPending ? "Removing…" : "Remove"}
        </Button>
      </div>
    </div>
  )
}
