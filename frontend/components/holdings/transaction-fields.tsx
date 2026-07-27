"use client"

import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { TransactionType } from "@/types"

export const TXN_TYPES: { value: TransactionType; label: string }[] = [
  { value: "buy", label: "Buy" },
  { value: "sell", label: "Sell" },
  { value: "sip", label: "SIP" },
  { value: "dividend", label: "Dividend" },
  { value: "switch", label: "Switch" },
]

export interface TransactionFieldsValue {
  type: TransactionType
  date: string
  quantity: string
  price: string
  charges: string
}

interface TransactionFieldsProps {
  value: TransactionFieldsValue
  onChange: (value: TransactionFieldsValue) => void
}

/** Shared Type/Quantity/Price/Date/Charges fields — used by both
 * AddTransactionForm and EditTransactionForm, which are identical except
 * for symbol/name/asset_class/sector, which only apply when adding. */
export function TransactionFields({ value, onChange }: TransactionFieldsProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="space-y-1.5">
        <Label className="text-xs">Type *</Label>
        <Select
          value={value.type}
          onValueChange={(v) => v && onChange({ ...value, type: v as TransactionType })}
        >
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
          value={value.quantity}
          onChange={(e) => onChange({ ...value, quantity: e.target.value })}
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
          value={value.price}
          onChange={(e) => onChange({ ...value, price: e.target.value })}
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
          value={value.date}
          onChange={(e) => onChange({ ...value, date: e.target.value })}
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
          value={value.charges}
          onChange={(e) => onChange({ ...value, charges: e.target.value })}
        />
      </div>
    </div>
  )
}
