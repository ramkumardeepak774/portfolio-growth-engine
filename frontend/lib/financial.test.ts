import { describe, expect, it } from "vitest"
import {
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
