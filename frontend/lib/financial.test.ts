import { describe, expect, it } from "vitest"
import {
  applyStressScenario,
  calcAlpha,
  calcBeta,
  calcCAGR,
  calcMaxDrawdown,
  calcSharpe,
  calcVolatility,
  calcXIRR,
  generateInsights,
  toDailyReturns,
  toDrawdownSeries,
  toMonthlyReturns,
  toRollingReturns,
  projectGoalValue,
  goalMilestones,
} from "./financial"

const ONE_YEAR_MS = 365.25 * 24 * 3600 * 1000

describe("calcCAGR", () => {
  it("doubles in one year -> 100%", () => {
    expect(calcCAGR(100, 200, 1)).toBeCloseTo(100, 6)
  })

  it("flat growth -> 0%", () => {
    expect(calcCAGR(100, 100, 5)).toBeCloseTo(0, 6)
  })

  it("10% CAGR over 10 years reconstructs correctly", () => {
    const final = 100 * 1.1 ** 10
    expect(calcCAGR(100, final, 10)).toBeCloseTo(10, 6)
  })

  it("returns 0 for non-positive initial", () => {
    expect(calcCAGR(0, 200, 5)).toBe(0)
    expect(calcCAGR(-100, 200, 5)).toBe(0)
  })

  it("returns 0 for non-positive years", () => {
    expect(calcCAGR(100, 200, 0)).toBe(0)
    expect(calcCAGR(100, 200, -1)).toBe(0)
  })

  it("handles a loss", () => {
    expect(calcCAGR(200, 100, 1)).toBeCloseTo(-50, 6)
  })
})

describe("calcXIRR", () => {
  it("returns null with fewer than 2 cashflows", () => {
    expect(calcXIRR([{ amount: -100, date: new Date() }])).toBeNull()
  })

  it("converges to 10% for a simple one-year round trip", () => {
    const d0 = new Date(2024, 0, 1)
    const d1 = new Date(d0.getTime() + ONE_YEAR_MS)
    const result = calcXIRR([
      { amount: -100, date: d0 },
      { amount: 110, date: d1 },
    ])
    expect(result).not.toBeNull()
    expect(result!).toBeCloseTo(10, 3)
  })

  it("returns a negative rate for a loss", () => {
    const d0 = new Date(2024, 0, 1)
    const d1 = new Date(d0.getTime() + ONE_YEAR_MS)
    const result = calcXIRR([
      { amount: -100, date: d0 },
      { amount: 90, date: d1 },
    ])
    expect(result).not.toBeNull()
    expect(result!).toBeLessThan(0)
  })
})

describe("calcVolatility", () => {
  it("returns null with fewer than 2 returns", () => {
    expect(calcVolatility([1])).toBeNull()
  })

  it("returns 0 for a constant return series", () => {
    expect(calcVolatility([1, 1, 1, 1])).toBeCloseTo(0, 6)
  })

  it("computes annualised volatility for a known series", () => {
    const returns = [1, -1, 1, -1]
    const mean = 0
    const variance = returns.reduce((a, r) => a + (r - mean) ** 2, 0) / (returns.length - 1)
    const expected = Math.sqrt(variance) * Math.sqrt(252) * 100
    expect(calcVolatility(returns)).toBeCloseTo(expected, 6)
  })
})

describe("calcMaxDrawdown", () => {
  it("returns null with fewer than 2 values", () => {
    expect(calcMaxDrawdown([100])).toBeNull()
  })

  it("computes the worst peak-to-trough decline", () => {
    // peak 120 -> trough 80 = 33.33% drawdown, later recovery to a new peak
    const dd = calcMaxDrawdown([100, 120, 80, 90, 150])
    expect(dd).toBeCloseTo(((120 - 80) / 120) * 100, 6)
  })

  it("returns 0 for a monotonically increasing series", () => {
    expect(calcMaxDrawdown([100, 110, 120, 130])).toBe(0)
  })
})

describe("calcSharpe", () => {
  it("returns null when volatility is zero or negative", () => {
    expect(calcSharpe(12, 6.5, 0)).toBeNull()
    expect(calcSharpe(12, 6.5, -1)).toBeNull()
  })

  it("computes excess return over volatility", () => {
    expect(calcSharpe(12, 6.5, 10)).toBeCloseTo(0.55, 6)
  })
})

describe("calcBeta", () => {
  it("returns null with fewer than 2 points", () => {
    expect(calcBeta([1], [1])).toBeNull()
  })

  it("returns null when benchmark has zero variance", () => {
    expect(calcBeta([1, 2, 3], [5, 5, 5])).toBeNull()
  })

  it("computes beta = 2 for a perfectly correlated 2x series", () => {
    const benchmark = [1, 2, 3, 4]
    const portfolio = benchmark.map((v) => v * 2)
    expect(calcBeta(portfolio, benchmark)).toBeCloseTo(2, 6)
  })

  it("truncates to the shorter series length", () => {
    const benchmark = [1, 2, 3, 4, 5]
    const portfolio = [2, 4, 6]
    expect(calcBeta(portfolio, benchmark)).toBeCloseTo(2, 6)
  })
})

describe("calcAlpha", () => {
  it("computes alpha against CAPM expected return", () => {
    // alpha = 20 - (6.5 + 1.2 * (15 - 6.5)) = 3.3
    expect(calcAlpha(20, 15, 1.2)).toBeCloseTo(3.3, 6)
  })

  it("respects a custom risk-free rate", () => {
    expect(calcAlpha(20, 15, 1, 0)).toBeCloseTo(5, 6)
  })
})

describe("toDailyReturns", () => {
  it("converts a price series to percentage returns", () => {
    expect(toDailyReturns([100, 110, 121])).toEqual([10, 10])
  })

  it("returns an empty array for a single price", () => {
    expect(toDailyReturns([100])).toEqual([])
  })

  it("skips a zero previous price to avoid division by zero", () => {
    expect(toDailyReturns([0, 100])).toEqual([])
  })
})

describe("toDrawdownSeries", () => {
  it("tracks running peak and drawdown percentage", () => {
    const series = toDrawdownSeries([100, 120, 80])
    expect(series[0].index).toBe(0)
    expect(series[0].drawdown).toBeCloseTo(0, 6)
    expect(series[1].index).toBe(1)
    expect(series[1].drawdown).toBeCloseTo(0, 6)
    expect(series[2].drawdown).toBeCloseTo(-((120 - 80) / 120) * 100, 6)
  })

  it("handles an empty series without throwing", () => {
    expect(toDrawdownSeries([])).toEqual([])
  })
})

describe("toMonthlyReturns", () => {
  it("returns empty for fewer than 2 points", () => {
    expect(toMonthlyReturns([])).toEqual([])
    expect(toMonthlyReturns([{ date: "2025-01-15", value: 100 }])).toEqual([])
  })

  it("skips the first month (no prior anchor) and returns month-over-month % change", () => {
    const series = [
      { date: "2025-01-31", value: 100 },
      { date: "2025-02-28", value: 110 },
      { date: "2025-03-31", value: 99 },
    ]
    const result = toMonthlyReturns(series)
    expect(result).toEqual([
      { year: 2025, month: 2, return_pct: 10 },
      { year: 2025, month: 3, return_pct: -10 },
    ])
  })

  it("uses the last value seen within a month (month-end snapshot)", () => {
    const series = [
      { date: "2025-01-05", value: 100 },
      { date: "2025-01-31", value: 105 },
      { date: "2025-02-10", value: 120 },
      { date: "2025-02-28", value: 126 },
    ]
    const result = toMonthlyReturns(series)
    expect(result).toEqual([{ year: 2025, month: 2, return_pct: 20 }])
  })

  it("spans multiple years correctly", () => {
    const series = [
      { date: "2024-12-31", value: 100 },
      { date: "2025-01-31", value: 105 },
    ]
    const result = toMonthlyReturns(series)
    expect(result).toEqual([{ year: 2025, month: 1, return_pct: 5 }])
  })
})

describe("toRollingReturns", () => {
  it("returns empty for fewer than 2 points", () => {
    expect(toRollingReturns([], 1)).toEqual([])
  })

  it("returns null (a gap) until a full window of history is available", () => {
    const series = [
      { date: "2024-01-01", value: 100 },
      { date: "2024-06-01", value: 110 },
      { date: "2024-12-31", value: 121 },
    ]
    const result = toRollingReturns(series, 1)
    expect(result.every((r) => r.rolling_cagr_pct === null)).toBe(true)
  })

  it("computes rolling CAGR once the window is available", () => {
    const series = [
      { date: "2023-01-01", value: 100 },
      { date: "2024-01-10", value: 110 },
    ]
    const result = toRollingReturns(series, 1)
    expect(result[0].rolling_cagr_pct).toBeNull()
    expect(result[1].rolling_cagr_pct).toBeCloseTo(10, 0)
  })

  it("leaves a gap (null) rather than a false zero when history is insufficient", () => {
    const series = [
      { date: "2024-01-01", value: 100 },
      { date: "2024-02-01", value: 105 },
    ]
    const result = toRollingReturns(series, 5)
    expect(result.every((r) => r.rolling_cagr_pct === null)).toBe(true)
  })
})

describe("generateInsights", () => {
  const base = {
    sectorAllocation: {},
    assetClassAllocation: { equity_large_cap: 30 },
    beta: 1.0,
    maxDrawdown: 10,
    cagr: 5,
  }

  it("flags heavy sector concentration above 40%", () => {
    const insights = generateInsights({ ...base, sectorAllocation: { IT: 45 } })
    expect(insights.some((i) => i.title.includes("IT concentration"))).toBe(true)
  })

  it("flags high beta above 1.3", () => {
    const insights = generateInsights({ ...base, beta: 1.5 })
    expect(insights.some((i) => i.title === "High market sensitivity")).toBe(true)
  })

  it("flags significant drawdown above 25%", () => {
    const insights = generateInsights({ ...base, maxDrawdown: 30 })
    expect(insights.some((i) => i.title === "Significant max drawdown")).toBe(true)
  })

  it("flags low large-cap allocation below 20%", () => {
    const insights = generateInsights({ ...base, assetClassAllocation: { equity_large_cap: 10 } })
    expect(insights.some((i) => i.title === "Low large-cap allocation")).toBe(true)
  })

  it("flags top-3 concentration above 60%", () => {
    const insights = generateInsights({ ...base, top3Pct: 70 })
    expect(insights.some((i) => i.title === "Top 3 holdings dominate")).toBe(true)
  })

  it("celebrates strong CAGR above 15%", () => {
    const insights = generateInsights({ ...base, cagr: 18 })
    expect(insights.some((i) => i.title === "Strong CAGR")).toBe(true)
  })

  it("falls back to a balanced message when nothing triggers", () => {
    const insights = generateInsights({
      sectorAllocation: {},
      assetClassAllocation: { equity_large_cap: 30 },
      beta: 1.0,
      maxDrawdown: 5,
      cagr: 8,
    })
    expect(insights).toEqual([
      {
        type: "success",
        title: "Portfolio looks balanced",
        description: "No major risk concentrations detected at this time.",
      },
    ])
  })
})

describe("applyStressScenario", () => {
  it("applies the shock proportionally to direct equity holdings", () => {
    const holdings = [
      { symbol: "RELIANCE", asset_class: "equity_large_cap", current_value: 100000 },
    ]
    const result = applyStressScenario(holdings, -30)
    expect(result[0].stressed_value).toBeCloseTo(70000, 6)
    expect(result[0].affected).toBe(true)
  })

  it("leaves non-equity holdings unaffected", () => {
    const holdings = [
      { symbol: "PPFAS_FLEXICAP", asset_class: "mf_equity", current_value: 50000 },
      { symbol: "GOLDBEES", asset_class: "gold", current_value: 20000 },
    ]
    const result = applyStressScenario(holdings, -30)
    expect(result[0].affected).toBe(false)
    expect(result[0].stressed_value).toBe(50000)
    expect(result[1].affected).toBe(false)
    expect(result[1].stressed_value).toBe(20000)
  })

  it("covers all four equity asset classes", () => {
    const holdings = [
      { symbol: "A", asset_class: "equity_large_cap", current_value: 100 },
      { symbol: "B", asset_class: "equity_mid_cap", current_value: 100 },
      { symbol: "C", asset_class: "equity_small_cap", current_value: 100 },
      { symbol: "D", asset_class: "equity_micro_cap", current_value: 100 },
    ]
    const result = applyStressScenario(holdings, -10)
    expect(result.every((r) => r.affected && r.stressed_value === 90)).toBe(true)
  })

  it("handles an empty holdings list", () => {
    expect(applyStressScenario([], -30)).toEqual([])
  })

  it("a mixed portfolio's total stressed value only reflects the equity drop", () => {
    const holdings = [
      { symbol: "RELIANCE", asset_class: "equity_large_cap", current_value: 100000 },
      { symbol: "GOLDBEES", asset_class: "gold", current_value: 50000 },
    ]
    const result = applyStressScenario(holdings, -20)
    const total = result.reduce((acc, r) => acc + r.stressed_value, 0)
    expect(total).toBeCloseTo(80000 + 50000, 6) // equity drops 20%, gold untouched
  })

  it("a positive shockPct models a rally, not just a crash", () => {
    const holdings = [{ symbol: "RELIANCE", asset_class: "equity_large_cap", current_value: 100000 }]
    const result = applyStressScenario(holdings, 10)
    expect(result[0].stressed_value).toBeCloseTo(110000, 6)
  })
})

describe("projectGoalValue", () => {
  it("doubles in one year at 100% CAGR", () => {
    expect(projectGoalValue(100000, 100, 1)).toBeCloseTo(200000, 6)
  })

  it("compounds correctly over multiple years", () => {
    // 500000 at 20% for 10 years
    expect(projectGoalValue(500000, 20, 10)).toBeCloseTo(500000 * 1.2 ** 10, 6)
  })

  it("returns the current value unchanged for zero years", () => {
    expect(projectGoalValue(500000, 41.4, 0)).toBe(500000)
  })

  it("returns the current value unchanged for negative years", () => {
    expect(projectGoalValue(500000, 41.4, -5)).toBe(500000)
  })

  it("handles a negative CAGR (a declining scenario)", () => {
    expect(projectGoalValue(100000, -10, 1)).toBeCloseTo(90000, 6)
  })
})

describe("goalMilestones", () => {
  it("returns one entry per whole year, years 1..N", () => {
    const result = goalMilestones(100000, 20, 5)
    expect(result.map((m) => m.year)).toEqual([1, 2, 3, 4, 5])
  })

  it("each milestone matches projectGoalValue for that year", () => {
    const result = goalMilestones(500000, 30, 3)
    result.forEach((m) => {
      expect(m.projectedValue).toBeCloseTo(projectGoalValue(500000, 30, m.year), 6)
    })
  })

  it("returns an empty array for zero years", () => {
    expect(goalMilestones(100000, 20, 0)).toEqual([])
  })

  it("floors a fractional years-remaining input", () => {
    expect(goalMilestones(100000, 20, 3.9)).toHaveLength(3)
  })
})
