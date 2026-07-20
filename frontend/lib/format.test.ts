import { describe, expect, it } from "vitest"
import { formatCompact, formatDate, formatINR, formatPct, formatRatio, pnlColor } from "./format"

describe("formatINR", () => {
  it("formats as a currency string by default", () => {
    expect(formatINR(1234)).toBe("₹1,234")
  })

  it("rounds to whole rupees", () => {
    expect(formatINR(1234.56)).toBe("₹1,235")
  })

  describe("compact mode", () => {
    it("abbreviates crores", () => {
      expect(formatINR(2_50_00_000, true)).toBe("₹2.50Cr")
    })

    it("abbreviates lakhs", () => {
      expect(formatINR(5_50_000, true)).toBe("₹5.50L")
    })

    it("abbreviates thousands", () => {
      expect(formatINR(15_000, true)).toBe("₹15.0K")
    })

    it("falls back to full currency format below 1000", () => {
      expect(formatINR(500, true)).toBe("₹500")
    })

    it("handles negative values", () => {
      expect(formatINR(-2_50_00_000, true)).toBe("₹-2.50Cr")
    })
  })
})

describe("formatPct", () => {
  it("prefixes a positive value with +", () => {
    expect(formatPct(5.4321)).toBe("+5.43%")
  })

  it("does not prefix a negative value (sign is already there)", () => {
    expect(formatPct(-3.1)).toBe("-3.10%")
  })

  it("does not prefix zero", () => {
    expect(formatPct(0)).toBe("0.00%")
  })

  it("respects a custom decimals count", () => {
    expect(formatPct(5.4321, 0)).toBe("+5%")
  })
})

describe("formatDate", () => {
  it("formats an ISO date string", () => {
    expect(formatDate("2026-07-20")).toBe("20 Jul 2026")
  })

  it("returns the raw string when parsing fails", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date")
  })
})

describe("pnlColor", () => {
  it("returns a green class for positive values", () => {
    expect(pnlColor(100)).toBe("text-emerald-500")
  })

  it("returns a red class for negative values", () => {
    expect(pnlColor(-100)).toBe("text-red-400")
  })

  it("returns a muted class for zero", () => {
    expect(pnlColor(0)).toBe("text-muted-foreground")
  })
})

describe("formatCompact", () => {
  it("abbreviates crores", () => {
    expect(formatCompact(2_50_00_000)).toBe("2.50Cr")
  })

  it("abbreviates lakhs", () => {
    expect(formatCompact(5_50_000)).toBe("5.50L")
  })

  it("abbreviates thousands", () => {
    expect(formatCompact(15_000)).toBe("15.0K")
  })

  it("falls back to a plain decimal below 1000", () => {
    expect(formatCompact(500)).toBe("500.00")
  })
})

describe("formatRatio", () => {
  it("formats a number to the given decimals", () => {
    expect(formatRatio(1.23456)).toBe("1.23")
    expect(formatRatio(1.23456, 3)).toBe("1.235")
  })

  it("returns an em dash for null or undefined", () => {
    expect(formatRatio(null)).toBe("—")
    expect(formatRatio(undefined)).toBe("—")
  })
})
