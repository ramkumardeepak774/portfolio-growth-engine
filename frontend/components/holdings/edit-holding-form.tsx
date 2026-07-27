"use client"

import { useState } from "react"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ASSET_CLASSES } from "@/lib/constants"
import { useUpdateHolding } from "@/hooks/use-portfolio"
import { AlertTriangle } from "lucide-react"

interface EditableHolding {
  symbol: string
  name: string
  asset_class: string
  sector: string | null
}

export function EditHoldingForm({
  holding,
  onClose,
}: {
  holding: EditableHolding
  onClose: () => void
}) {
  const { mutate, isPending, error } = useUpdateHolding()
  const [name, setName] = useState(holding.name)
  const [assetClass, setAssetClass] = useState(holding.asset_class)
  const [sector, setSector] = useState(holding.sector ?? "")

  const assetClassChanged = assetClass !== holding.asset_class
  const isValid = name.trim().length > 0

  const handleSubmit = () => {
    if (!isValid) return
    mutate(
      {
        symbol: holding.symbol,
        payload: {
          name: name.trim(),
          asset_class: assetClass,
          sector: sector.trim() || undefined,
        },
      },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="space-y-4 mt-2">
      <div className="space-y-1.5">
        <Label htmlFor="edit-name" className="text-xs">
          Name *
        </Label>
        <Input id="edit-name" className="h-8 text-sm" value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div className="space-y-1.5">
        <Label className="text-xs">Asset Class</Label>
        <Select value={assetClass} onValueChange={(v) => v && setAssetClass(v)}>
          <SelectTrigger className="h-8 text-sm">
            <SelectValue />
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
      <div className="space-y-1.5">
        <Label htmlFor="edit-sector" className="text-xs">
          Sector
        </Label>
        <Input
          id="edit-sector"
          className="h-8 text-sm"
          placeholder="Energy"
          value={sector}
          onChange={(e) => setSector(e.target.value)}
        />
      </div>

      {assetClassChanged && (
        <p className="text-xs text-amber-500 bg-amber-500/10 px-3 py-2 rounded-md flex items-start gap-1.5">
          <AlertTriangle className="size-3.5 mt-0.5 shrink-0" />
          Changing the asset class is a reclassification, not cosmetic — it affects tax-report
          bucketing and growth-chart calculations for this holding.
        </p>
      )}

      {error && (
        <p className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-md">{error.message}</p>
      )}

      <Button className="w-full h-8 text-sm mt-2" disabled={!isValid || isPending} onClick={handleSubmit}>
        {isPending ? "Saving…" : "Save Changes"}
      </Button>
    </div>
  )
}
