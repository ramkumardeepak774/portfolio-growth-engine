"use client"

import { Button } from "@/components/ui/button"
import { useDeleteHolding } from "@/hooks/use-portfolio"

interface DeletableHolding {
  symbol: string
  quantity: number
}

export function DeleteHoldingConfirm({
  holding,
  onClose,
  onDeleted,
}: {
  holding: DeletableHolding
  onClose: () => void
  onDeleted?: () => void
}) {
  const { mutate, isPending, error } = useDeleteHolding()
  const hasQuantity = Math.abs(holding.quantity) > 1e-9

  const handleDelete = () => {
    mutate(holding.symbol, {
      onSuccess: () => {
        onClose()
        onDeleted?.()
      },
    })
  }

  return (
    <div className="space-y-4 mt-2">
      <p className="text-sm text-muted-foreground">
        Hide <span className="font-medium text-foreground">{holding.symbol}</span> from your
        holdings? This isn&apos;t permanent — adding a new transaction for it later brings it back.
      </p>

      {hasQuantity && (
        <p className="text-xs text-amber-500 bg-amber-500/10 px-3 py-2 rounded-md">
          This holding still has a nonzero quantity ({holding.quantity.toLocaleString("en-IN")}{" "}
          units) — hiding it removes it from every dashboard view even though the position isn&apos;t
          fully exited.
        </p>
      )}

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
          {isPending ? "Hiding…" : "Hide Holding"}
        </Button>
      </div>
    </div>
  )
}
