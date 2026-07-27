"use client"

import { useMemo, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Header } from "@/components/layout/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
} from "@/components/ui/dialog"
import { PortfolioGrowthChart } from "@/components/charts/portfolio-growth-chart"
import { TransactionFields, type TransactionFieldsValue } from "@/components/holdings/transaction-fields"
import { EditHoldingForm } from "@/components/holdings/edit-holding-form"
import { DeleteHoldingConfirm } from "@/components/holdings/delete-holding-confirm"
import { useHoldingDetail, useStockPrices, useUpdateTransaction, useDeleteTransaction } from "@/hooks/use-portfolio"
import { formatINR, formatPct, formatDate, pnlColor } from "@/lib/format"
import { ArrowLeft, Pencil, Trash2 } from "lucide-react"
import type { TransactionRow } from "@/types"

const TXN_TYPE_LABELS: Record<string, string> = {
  buy: "Buy",
  sell: "Sell",
  sip: "SIP",
  dividend: "Dividend",
  switch: "Switch",
}

export default function HoldingDetailPage() {
  const params = useParams<{ symbol: string }>()
  const symbol = decodeURIComponent(params.symbol ?? "")
  const router = useRouter()

  const { data: holding, isLoading, isError } = useHoldingDetail(symbol)
  const { data: prices, isLoading: pricesLoading } = useStockPrices(symbol, "1y")
  const [editingTxn, setEditingTxn] = useState<TransactionRow | null>(null)
  const [deletingTxn, setDeletingTxn] = useState<TransactionRow | null>(null)
  const [editingHolding, setEditingHolding] = useState(false)
  const [deletingHolding, setDeletingHolding] = useState(false)

  const priceChartData = useMemo(() => {
    if (!prices?.length) return []
    return prices.map((p) => ({ date: p.Date.split("T")[0], value: p.Close }))
  }, [prices])

  if (isError) {
    return (
      <div className="flex flex-col">
        <Header title="Holding not found" />
        <div className="p-6">
          <Card>
            <CardContent className="p-8 text-center space-y-3">
              <p className="text-sm text-muted-foreground">
                No active holding for symbol &ldquo;{symbol}&rdquo;.
              </p>
              <Button variant="outline" size="sm" onClick={() => router.push("/holdings")}>
                <ArrowLeft className="size-3.5 mr-1.5" /> Back to Holdings
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col">
      <Header
        title={isLoading ? "Loading…" : holding?.symbol ?? symbol}
        subtitle={holding?.name}
      />

      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="sm" className="w-fit -ml-2" onClick={() => router.push("/holdings")}>
            <ArrowLeft className="size-3.5 mr-1.5" /> Back to Holdings
          </Button>
          {holding && (
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setEditingHolding(true)}>
                <Pencil className="size-3.5 mr-1.5" /> Edit
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-red-400 hover:text-red-400"
                onClick={() => setDeletingHolding(true)}
              >
                <Trash2 className="size-3.5 mr-1.5" /> Hide
              </Button>
            </div>
          )}
        </div>

        {/* KPI strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Quantity", value: isLoading ? null : holding?.quantity.toLocaleString("en-IN") },
            { label: "Invested", value: isLoading ? null : formatINR(holding?.invested_amount ?? 0, true) },
            { label: "Current Value", value: isLoading ? null : formatINR(holding?.current_value ?? 0, true) },
            {
              label: "P&L",
              value: isLoading ? null : formatINR(holding?.pnl ?? 0, true),
              pct: holding?.pnl_percent,
            },
          ].map((kpi) => (
            <Card key={kpi.label}>
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground">{kpi.label}</p>
                {kpi.value === null ? (
                  <Skeleton className="h-6 w-20 mt-1" />
                ) : (
                  <p className={`text-lg font-semibold mt-0.5 ${kpi.pct !== undefined ? pnlColor(kpi.pct) : ""}`}>
                    {kpi.value}
                    {kpi.pct !== undefined && (
                      <span className="text-xs font-normal ml-1.5">({formatPct(kpi.pct)})</span>
                    )}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {holding && (
          <div className="flex items-center gap-2">
            {holding.sector && <Badge variant="secondary">{holding.sector}</Badge>}
            <Badge variant="outline">{holding.asset_class.replace(/_/g, " ")}</Badge>
          </div>
        )}

        {/* Price chart */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Price History (1Y)</CardTitle>
          </CardHeader>
          <CardContent>
            <PortfolioGrowthChart data={priceChartData} loading={pricesLoading} height={240} />
          </CardContent>
        </Card>

        {/* Transaction history */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Transaction History</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-6 text-xs">Date</TableHead>
                  <TableHead className="text-xs">Type</TableHead>
                  <TableHead className="text-xs">Quantity</TableHead>
                  <TableHead className="text-xs">Price</TableHead>
                  <TableHead className="text-xs">Charges</TableHead>
                  <TableHead className="text-xs">Amount</TableHead>
                  <TableHead className="text-xs pr-6 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 7 }).map((_, j) => (
                        <TableCell key={j}>
                          <Skeleton className="h-4 w-full" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : !holding?.transactions.length ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12 text-sm text-muted-foreground">
                      No transactions recorded for this holding.
                    </TableCell>
                  </TableRow>
                ) : (
                  holding.transactions.map((t, i) => (
                    <TableRow key={t.id ?? i}>
                      <TableCell className="pl-6 text-sm">{formatDate(t.date)}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                          {TXN_TYPE_LABELS[t.type] ?? t.type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">{t.quantity.toLocaleString("en-IN")}</TableCell>
                      <TableCell className="text-sm">{formatINR(t.price)}</TableCell>
                      <TableCell className="text-sm">{formatINR(t.charges)}</TableCell>
                      <TableCell className="text-sm font-medium">{formatINR(t.amount)}</TableCell>
                      <TableCell className="pr-6">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-7"
                            disabled={t.id === null}
                            onClick={() => setEditingTxn(t)}
                          >
                            <Pencil className="size-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-7 text-red-400 hover:text-red-400"
                            disabled={t.id === null}
                            onClick={() => setDeletingTxn(t)}
                          >
                            <Trash2 className="size-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <Dialog open={editingTxn !== null} onOpenChange={(open) => !open && setEditingTxn(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Transaction</DialogTitle>
          </DialogHeader>
          {editingTxn && (
            <EditTransactionForm transaction={editingTxn} onClose={() => setEditingTxn(null)} />
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={deletingTxn !== null} onOpenChange={(open) => !open && setDeletingTxn(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Transaction</DialogTitle>
          </DialogHeader>
          {deletingTxn && (
            <DeleteTransactionConfirm transaction={deletingTxn} onClose={() => setDeletingTxn(null)} />
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={editingHolding} onOpenChange={setEditingHolding}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Holding</DialogTitle>
          </DialogHeader>
          {holding && <EditHoldingForm holding={holding} onClose={() => setEditingHolding(false)} />}
        </DialogContent>
      </Dialog>

      <Dialog open={deletingHolding} onOpenChange={setDeletingHolding}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Hide Holding</DialogTitle>
          </DialogHeader>
          {holding && (
            <DeleteHoldingConfirm
              holding={holding}
              onClose={() => setDeletingHolding(false)}
              onDeleted={() => router.push("/holdings")}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

function EditTransactionForm({
  transaction,
  onClose,
}: {
  transaction: TransactionRow
  onClose: () => void
}) {
  const { mutate, isPending, error } = useUpdateTransaction()
  const [form, setForm] = useState<TransactionFieldsValue>({
    type: transaction.type as TransactionFieldsValue["type"],
    date: transaction.date,
    quantity: String(transaction.quantity),
    price: String(transaction.price),
    charges: String(transaction.charges),
  })

  const isValid = form.date && Number(form.quantity) > 0 && Number(form.price) > 0

  const handleSubmit = () => {
    if (!isValid || transaction.id === null) return
    mutate(
      {
        id: transaction.id,
        payload: {
          type: form.type,
          date: form.date,
          quantity: Number(form.quantity),
          price: Number(form.price),
          charges: form.charges ? Number(form.charges) : 0,
        },
      },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="space-y-4 mt-2">
      <TransactionFields value={form} onChange={setForm} />

      {error && (
        <p className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-md">{error.message}</p>
      )}

      <Button className="w-full h-8 text-sm mt-2" disabled={!isValid || isPending} onClick={handleSubmit}>
        {isPending ? "Saving…" : "Save Changes"}
      </Button>
    </div>
  )
}

function DeleteTransactionConfirm({
  transaction,
  onClose,
}: {
  transaction: TransactionRow
  onClose: () => void
}) {
  const { mutate, isPending, error } = useDeleteTransaction()

  const handleDelete = () => {
    if (transaction.id === null) return
    mutate(transaction.id, { onSuccess: onClose })
  }

  return (
    <div className="space-y-4 mt-2">
      <p className="text-sm text-muted-foreground">
        Delete the {TXN_TYPE_LABELS[transaction.type] ?? transaction.type} of{" "}
        {transaction.quantity.toLocaleString("en-IN")} units on {formatDate(transaction.date)}? This
        can&apos;t be undone.
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
          onClick={handleDelete}
        >
          {isPending ? "Deleting…" : "Delete"}
        </Button>
      </div>
    </div>
  )
}
