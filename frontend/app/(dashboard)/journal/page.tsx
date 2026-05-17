"use client"

import { useState } from "react"
import { format, parseISO } from "date-fns"
import { Header } from "@/components/layout/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
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
import { useJournalEntries, useCreateJournalEntry } from "@/hooks/use-journal"
import { Plus, BookOpen, CheckCircle2, Clock } from "lucide-react"
import type { JournalEntry, JournalAction, Conviction } from "@/types"

const ACTION_COLORS: Record<JournalAction, string> = {
  entry: "bg-emerald-500/10 text-emerald-500",
  exit: "bg-red-400/10 text-red-400",
  add: "bg-blue-400/10 text-blue-400",
  trim: "bg-amber-500/10 text-amber-500",
  hold: "bg-muted text-muted-foreground",
  watchlist: "bg-purple-400/10 text-purple-400",
}

const CONVICTION_COLORS: Record<Conviction, string> = {
  very_high: "text-emerald-500",
  high: "text-emerald-400",
  medium: "text-amber-500",
  low: "text-muted-foreground",
  speculative: "text-red-400",
}

function EntryCard({ entry }: { entry: JournalEntry }) {
  return (
    <Card className="hover:border-border/80 transition-colors">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm">{entry.symbol}</span>
            <Badge className={`text-[10px] px-1.5 py-0 border-0 ${ACTION_COLORS[entry.action]}`}>
              {entry.action.toUpperCase()}
            </Badge>
            {entry.reviewed ? (
              <CheckCircle2 className="size-3.5 text-emerald-500" />
            ) : (
              <Clock className="size-3.5 text-muted-foreground" />
            )}
          </div>
          <div className="text-right text-xs text-muted-foreground">
            <p>{format(parseISO(entry.created_at), "dd MMM yyyy")}</p>
            <p className={`font-medium mt-0.5 ${CONVICTION_COLORS[entry.conviction]}`}>
              {entry.conviction.replace("_", " ")}
            </p>
          </div>
        </div>

        <p className="text-sm text-foreground mb-2 leading-relaxed">{entry.why}</p>

        {entry.thesis && (
          <p className="text-xs text-muted-foreground mb-3">{entry.thesis}</p>
        )}

        <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
          {entry.quantity > 0 && (
            <span>
              Qty: <strong className="text-foreground">{entry.quantity}</strong>
            </span>
          )}
          {entry.price > 0 && (
            <span>
              Price: <strong className="text-foreground">₹{entry.price.toLocaleString("en-IN")}</strong>
            </span>
          )}
          {entry.time_horizon && (
            <span>
              Horizon: <strong className="text-foreground">{entry.time_horizon}</strong>
            </span>
          )}
          {entry.rating != null && entry.rating > 0 && (
            <span>
              Rating: <strong className="text-foreground">{entry.rating}/10</strong>
            </span>
          )}
        </div>

        {entry.risk_factors?.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground mb-1.5">
              Risk Factors
            </p>
            <ul className="space-y-0.5">
              {entry.risk_factors.map((r, i) => (
                <li key={i} className="text-xs text-muted-foreground flex gap-1.5">
                  <span className="text-red-400 mt-0.5">•</span> {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {entry.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {entry.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-[10px] px-1.5 py-0">
                #{tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function EntrySkeleton() {
  return (
    <Card>
      <CardContent className="p-5 space-y-3">
        <div className="flex gap-2">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-12" />
        </div>
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-3/4" />
      </CardContent>
    </Card>
  )
}

function CreateEntryForm({ onClose }: { onClose: () => void }) {
  const { mutate, isPending } = useCreateJournalEntry()
  const [form, setForm] = useState({
    symbol: "",
    action: "entry" as JournalAction,
    why: "",
    thesis: "",
    conviction: "medium" as Conviction,
    quantity: "",
    price: "",
    time_horizon: "",
  })

  const handleSubmit = () => {
    if (!form.symbol || !form.why) return
    mutate(
      {
        symbol: form.symbol,
        action: form.action,
        why: form.why,
        thesis: form.thesis,
        conviction: form.conviction,
        quantity: Number(form.quantity) || 0,
        price: Number(form.price) || 0,
        time_horizon: form.time_horizon,
      },
      { onSuccess: () => onClose() },
    )
  }

  return (
    <div className="space-y-4 mt-2">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs">Symbol *</Label>
          <Input
            className="h-8 text-sm uppercase"
            placeholder="RELIANCE"
            value={form.symbol}
            onChange={(e) => setForm((s) => ({ ...s, symbol: e.target.value.toUpperCase() }))}
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Action *</Label>
          <Select
            value={form.action}
            onValueChange={(v) => setForm((s) => ({ ...s, action: v as JournalAction }))}
          >
            <SelectTrigger className="h-8 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(["entry", "exit", "add", "trim", "hold", "watchlist"] as JournalAction[]).map(
                (a) => (
                  <SelectItem key={a} value={a} className="text-sm">
                    {a.charAt(0).toUpperCase() + a.slice(1)}
                  </SelectItem>
                ),
              )}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-1.5">
        <Label className="text-xs">Why are you making this decision? * (document BEFORE acting)</Label>
        <textarea
          className="w-full h-20 text-sm rounded-md border border-input bg-background px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
          placeholder="Your reasoning…"
          value={form.why}
          onChange={(e) => setForm((s) => ({ ...s, why: e.target.value }))}
        />
      </div>

      <div className="space-y-1.5">
        <Label className="text-xs">Investment Thesis</Label>
        <textarea
          className="w-full h-16 text-sm rounded-md border border-input bg-background px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
          placeholder="Long-term thesis…"
          value={form.thesis}
          onChange={(e) => setForm((s) => ({ ...s, thesis: e.target.value }))}
        />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs">Conviction</Label>
          <Select
            value={form.conviction}
            onValueChange={(v) => setForm((s) => ({ ...s, conviction: v as Conviction }))}
          >
            <SelectTrigger className="h-8 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(["very_high", "high", "medium", "low", "speculative"] as Conviction[]).map((c) => (
                <SelectItem key={c} value={c} className="text-sm">
                  {c.replace("_", " ")}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Quantity</Label>
          <Input
            className="h-8 text-sm"
            type="number"
            placeholder="100"
            value={form.quantity}
            onChange={(e) => setForm((s) => ({ ...s, quantity: e.target.value }))}
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Price (₹)</Label>
          <Input
            className="h-8 text-sm"
            type="number"
            placeholder="2500"
            value={form.price}
            onChange={(e) => setForm((s) => ({ ...s, price: e.target.value }))}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label className="text-xs">Time Horizon</Label>
        <Input
          className="h-8 text-sm"
          placeholder="3-5 years"
          value={form.time_horizon}
          onChange={(e) => setForm((s) => ({ ...s, time_horizon: e.target.value }))}
        />
      </div>

      <Button
        className="w-full h-8 text-sm"
        onClick={handleSubmit}
        disabled={isPending || !form.symbol || !form.why}
      >
        {isPending ? "Saving…" : "Save Journal Entry"}
      </Button>
    </div>
  )
}

export default function JournalPage() {
  const { data: entries, isLoading } = useJournalEntries()
  const [open, setOpen] = useState(false)

  const reviewed = entries?.filter((e) => e.reviewed).length ?? 0
  const pending = entries?.filter((e) => !e.reviewed).length ?? 0

  return (
    <div className="flex flex-col">
      <Header title="Decision Journal" subtitle="Document your reasoning before every trade" />

      <div className="p-6 space-y-5">
        {/* Stats */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2 text-sm">
            <BookOpen className="size-4 text-muted-foreground" />
            <span className="font-medium">{entries?.length ?? 0}</span>
            <span className="text-muted-foreground">total entries</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="size-4 text-emerald-500" />
            <span className="font-medium">{reviewed}</span>
            <span className="text-muted-foreground">reviewed</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Clock className="size-4 text-amber-500" />
            <span className="font-medium">{pending}</span>
            <span className="text-muted-foreground">pending review</span>
          </div>
          <div className="ml-auto">
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg bg-primary text-primary-foreground px-2.5 h-8 text-xs font-medium transition-colors hover:bg-primary/90">
                <Plus className="size-3.5" /> New Entry
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>New Journal Entry</DialogTitle>
                </DialogHeader>
                <CreateEntryForm onClose={() => setOpen(false)} />
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Entries */}
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {isLoading ? (
            Array.from({ length: 6 }).map((_, i) => <EntrySkeleton key={i} />)
          ) : entries?.length === 0 ? (
            <Card className="md:col-span-2 xl:col-span-3">
              <CardContent className="py-16 text-center">
                <BookOpen className="size-8 mx-auto text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground">No journal entries yet.</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Document your reasoning before every trade — it makes you a better investor.
                </p>
              </CardContent>
            </Card>
          ) : (
            entries?.map((entry) => <EntryCard key={entry.id} entry={entry} />)
          )}
        </div>
      </div>
    </div>
  )
}
