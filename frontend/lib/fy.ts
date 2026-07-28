/** Indian financial year (Apr 1 - Mar 31) helpers, shared by the tax-report
 * and dividends pages, which both need the same FY-selector logic. */

export function currentFyOption(): string {
  const now = new Date()
  const startYear = now.getMonth() >= 3 ? now.getFullYear() : now.getFullYear() - 1 // getMonth() is 0-indexed, April = 3
  return `${startYear}-${String(startYear + 1).slice(2)}`
}

export function fyOptions(): string[] {
  const current = Number(currentFyOption().split("-")[0])
  return Array.from({ length: 6 }, (_, i) => {
    const startYear = current - i
    return `${startYear}-${String(startYear + 1).slice(2)}`
  })
}
