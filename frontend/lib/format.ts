import { format, parseISO } from "date-fns"

/** Format a number as Indian Rupees */
export function formatINR(value: number, compact = false): string {
  if (compact) {
    if (Math.abs(value) >= 1_00_00_000) return `₹${(value / 1_00_00_000).toFixed(2)}Cr`
    if (Math.abs(value) >= 1_00_000) return `₹${(value / 1_00_000).toFixed(2)}L`
    if (Math.abs(value) >= 1_000) return `₹${(value / 1_000).toFixed(1)}K`
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value)
}

/** Format a percentage with sign */
export function formatPct(value: number, decimals = 2): string {
  const sign = value > 0 ? "+" : ""
  return `${sign}${value.toFixed(decimals)}%`
}

/** Format a date string (ISO → readable) */
export function formatDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "dd MMM yyyy")
  } catch {
    return dateStr
  }
}

/** Return Tailwind colour classes for a P&L value */
export function pnlColor(value: number): string {
  if (value > 0) return "text-emerald-500"
  if (value < 0) return "text-red-400"
  return "text-muted-foreground"
}

/** Abbreviate large numbers */
export function formatCompact(value: number): string {
  if (Math.abs(value) >= 1_00_00_000) return `${(value / 1_00_00_000).toFixed(2)}Cr`
  if (Math.abs(value) >= 1_00_000) return `${(value / 1_00_000).toFixed(2)}L`
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  return value.toFixed(2)
}

/** Format a ratio (e.g. Sharpe, Beta) */
export function formatRatio(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined) return "—"
  return value.toFixed(decimals)
}
