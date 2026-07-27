/**
 * Financial calculation utilities.
 * All functions accept plain numbers and return numbers.
 */

/** Compound Annual Growth Rate */
export function calcCAGR(initial: number, final: number, years: number): number {
  if (initial <= 0 || years <= 0) return 0
  return ((final / initial) ** (1 / years) - 1) * 100
}

/**
 * XIRR — Newton-Raphson implementation for irregular cash-flows.
 * @param cashflows  Array of { amount, date } — outflows are negative, inflows positive
 * @returns Annualised IRR as a percentage, or null if it fails to converge
 */
export function calcXIRR(
  cashflows: Array<{ amount: number; date: Date }>,
  maxIter = 100,
  tol = 1e-6,
): number | null {
  if (cashflows.length < 2) return null

  const t0 = cashflows[0].date.getTime()
  const years = cashflows.map((cf) => (cf.date.getTime() - t0) / (365.25 * 24 * 3600 * 1000))
  const amounts = cashflows.map((cf) => cf.amount)

  const npv = (rate: number) =>
    amounts.reduce((acc, a, i) => acc + a / (1 + rate) ** years[i], 0)

  const dnpv = (rate: number) =>
    amounts.reduce((acc, a, i) => acc - (i * a * years[i]) / (1 + rate) ** (years[i] + 1), 0)

  let rate = 0.1
  for (let i = 0; i < maxIter; i++) {
    const f = npv(rate)
    const df = dnpv(rate)
    if (Math.abs(df) < 1e-12) break
    const next = rate - f / df
    if (Math.abs(next - rate) < tol) return next * 100
    rate = next
  }
  return null
}

/** Annualised Volatility from daily return series (as %) */
export function calcVolatility(dailyReturns: number[]): number | null {
  if (dailyReturns.length < 2) return null
  const mean = dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length
  const variance =
    dailyReturns.reduce((acc, r) => acc + (r - mean) ** 2, 0) / (dailyReturns.length - 1)
  return Math.sqrt(variance) * Math.sqrt(252) * 100 // annualise
}

/** Maximum Drawdown from a price/value series (%) */
export function calcMaxDrawdown(values: number[]): number | null {
  if (values.length < 2) return null
  let peak = values[0]
  let maxDD = 0
  for (const v of values) {
    if (v > peak) peak = v
    const dd = (peak - v) / peak
    if (dd > maxDD) maxDD = dd
  }
  return maxDD * 100
}

/** Sharpe Ratio — (portfolio return - risk-free) / volatility */
export function calcSharpe(
  portfolioReturnPct: number,
  riskFreePct: number,
  volatilityPct: number,
): number | null {
  if (volatilityPct <= 0) return null
  return (portfolioReturnPct - riskFreePct) / volatilityPct
}

/**
 * Beta — covariance(portfolio, benchmark) / variance(benchmark)
 * Both series should be daily returns (%).
 */
export function calcBeta(portfolioReturns: number[], benchmarkReturns: number[]): number | null {
  const n = Math.min(portfolioReturns.length, benchmarkReturns.length)
  if (n < 2) return null

  const pR = portfolioReturns.slice(0, n)
  const bR = benchmarkReturns.slice(0, n)

  const pMean = pR.reduce((a, b) => a + b, 0) / n
  const bMean = bR.reduce((a, b) => a + b, 0) / n

  let cov = 0
  let varB = 0
  for (let i = 0; i < n; i++) {
    cov += (pR[i] - pMean) * (bR[i] - bMean)
    varB += (bR[i] - bMean) ** 2
  }

  if (varB === 0) return null
  return cov / varB
}

/** Alpha = portfolio return − (risk-free + beta × (benchmark − risk-free)) */
export function calcAlpha(
  portfolioReturnPct: number,
  benchmarkReturnPct: number,
  beta: number,
  riskFreePct = 6.5, // India 10yr G-Sec approx
): number {
  return portfolioReturnPct - (riskFreePct + beta * (benchmarkReturnPct - riskFreePct))
}

/** Convert a price series to daily percentage returns */
export function toDailyReturns(prices: number[]): number[] {
  const returns: number[] = []
  for (let i = 1; i < prices.length; i++) {
    const prev = prices[i - 1]
    if (prev !== 0) returns.push(((prices[i] - prev) / prev) * 100)
  }
  return returns
}

/** Build drawdown series from a value series */
export function toDrawdownSeries(values: number[]): Array<{ index: number; drawdown: number }> {
  let peak = values[0] ?? 0
  return values.map((v, i) => {
    if (v > peak) peak = v
    const dd = peak > 0 ? -((peak - v) / peak) * 100 : 0
    return { index: i, drawdown: dd }
  })
}

export interface MonthlyReturn {
  year: number
  month: number // 1-12
  return_pct: number
}

/**
 * Bucket a daily value series into month-end snapshots and return the %
 * change month-over-month. Value-based, not cashflow-adjusted — a mid-month
 * SIP shows up as a return spike distinct from actual price movement.
 * The first month in the series has no prior anchor and is skipped.
 */
export function toMonthlyReturns(
  series: Array<{ date: string; value: number }>,
): MonthlyReturn[] {
  if (series.length < 2) return []

  const monthEnds = new Map<string, { year: number; month: number; value: number }>()
  for (const point of series) {
    const d = new Date(point.date)
    const year = d.getUTCFullYear()
    const month = d.getUTCMonth() + 1
    // series is date-ascending, so the last write per key is the month-end value
    monthEnds.set(`${year}-${month}`, { year, month, value: point.value })
  }

  const ordered = Array.from(monthEnds.values()).sort(
    (a, b) => a.year - b.year || a.month - b.month,
  )

  const result: MonthlyReturn[] = []
  for (let i = 1; i < ordered.length; i++) {
    const prev = ordered[i - 1]
    const curr = ordered[i]
    if (prev.value <= 0) continue
    result.push({
      year: curr.year,
      month: curr.month,
      return_pct: ((curr.value - prev.value) / prev.value) * 100,
    })
  }
  return result
}

export interface RollingReturnPoint {
  date: string
  rolling_cagr_pct: number | null
}

const MS_PER_YEAR = 365.25 * 24 * 3600 * 1000

/**
 * Rolling CAGR over a fixed trailing window (e.g. 1/3/5 years), walked across
 * a value series. Points before a full window of history is available are
 * `null` (a gap), not 0 — a false zero would misread as "flat returns."
 * Value-based like toMonthlyReturns, not cashflow-adjusted.
 */
export function toRollingReturns(
  series: Array<{ date: string; value: number }>,
  windowYears: number,
): RollingReturnPoint[] {
  if (series.length < 2) return []

  const points = series.map((p) => ({ date: p.date, value: p.value, time: new Date(p.date).getTime() }))
  const windowMs = windowYears * MS_PER_YEAR

  let startIdx = 0
  const result: RollingReturnPoint[] = []
  for (let i = 0; i < points.length; i++) {
    const targetTime = points[i].time - windowMs
    while (startIdx + 1 < points.length && points[startIdx + 1].time <= targetTime) {
      startIdx++
    }
    const start = points[startIdx]
    const years = (points[i].time - start.time) / MS_PER_YEAR
    if (start.time > targetTime || start.value <= 0 || years <= 0) {
      result.push({ date: points[i].date, rolling_cagr_pct: null })
      continue
    }
    result.push({ date: points[i].date, rolling_cagr_pct: calcCAGR(start.value, points[i].value, years) })
  }
  return result
}

/** Rule-based portfolio insights */
export function generateInsights(params: {
  sectorAllocation: Record<string, number>
  assetClassAllocation: Record<string, number>
  beta: number | null
  maxDrawdown: number | null
  cagr: number
  top3Pct?: number
}): Array<{ type: "warning" | "info" | "success"; title: string; description: string }> {
  const insights: Array<{ type: "warning" | "info" | "success"; title: string; description: string }> = []

  // Sector concentration
  const sectors = Object.entries(params.sectorAllocation)
  for (const [sector, pct] of sectors) {
    if (pct > 40) {
      insights.push({
        type: "warning",
        title: `Heavy ${sector} concentration`,
        description: `${sector} represents ${pct.toFixed(1)}% of portfolio — consider diversifying.`,
      })
    }
  }

  // Beta
  if (params.beta !== null && params.beta > 1.3) {
    insights.push({
      type: "warning",
      title: "High market sensitivity",
      description: `Portfolio beta of ${params.beta.toFixed(2)} means higher volatility than the market.`,
    })
  }

  // Drawdown
  if (params.maxDrawdown !== null && params.maxDrawdown > 25) {
    insights.push({
      type: "warning",
      title: "Significant max drawdown",
      description: `Max drawdown of ${params.maxDrawdown.toFixed(1)}% — review risk management.`,
    })
  }

  // Large cap allocation check
  const largeCap = params.assetClassAllocation["equity_large_cap"] ?? 0
  if (largeCap < 20) {
    insights.push({
      type: "info",
      title: "Low large-cap allocation",
      description: `Large-cap exposure is only ${largeCap.toFixed(1)}% — consider adding stability.`,
    })
  }

  // Top 3 concentration
  if (params.top3Pct && params.top3Pct > 60) {
    insights.push({
      type: "warning",
      title: "Top 3 holdings dominate",
      description: `Top 3 positions account for ${params.top3Pct.toFixed(1)}% of portfolio value.`,
    })
  }

  // Positive CAGR
  if (params.cagr > 15) {
    insights.push({
      type: "success",
      title: "Strong CAGR",
      description: `Portfolio is compounding at ${params.cagr.toFixed(1)}% per year — above market average.`,
    })
  }

  if (insights.length === 0) {
    insights.push({
      type: "success",
      title: "Portfolio looks balanced",
      description: "No major risk concentrations detected at this time.",
    })
  }

  return insights
}

/** Direct equity asset classes — a market crash hits these; mutual funds,
 * gold, FD/PPF/EPF/NPS, real estate, crypto, and cash are far more
 * resilient (or simply uncorrelated) and are left unaffected rather than
 * guessed at. Mirrors _PRICEABLE_ASSET_CLASSES in src/analyzer.py, but
 * this is frontend-local since the stress test has no backend involvement. */
export const EQUITY_ASSET_CLASSES = [
  "equity_large_cap",
  "equity_mid_cap",
  "equity_small_cap",
  "equity_micro_cap",
]

export interface StressTestRow {
  symbol: string
  asset_class: string
  current_value: number
  stressed_value: number
  affected: boolean
}

/** Apply a uniform % shock (e.g. -30 for a 30% drop) to direct equity
 * holdings only. Non-equity holdings are returned unchanged with
 * affected: false, so the UI can show them as explicitly untouched rather
 * than silently including them in the "after crash" total. */
export function applyStressScenario(
  holdings: Array<{ symbol: string; asset_class: string; current_value: number }>,
  shockPct: number,
): StressTestRow[] {
  return holdings.map((h) => {
    const affected = EQUITY_ASSET_CLASSES.includes(h.asset_class)
    return {
      symbol: h.symbol,
      asset_class: h.asset_class,
      current_value: h.current_value,
      stressed_value: affected ? h.current_value * (1 + shockPct / 100) : h.current_value,
      affected,
    }
  })
}
