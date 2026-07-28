import { describe, expect, it, vi, afterEach } from "vitest"
import { currentFyOption, fyOptions } from "./fy"

describe("currentFyOption", () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it("returns the FY starting this year when the date is in or after April", () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 5, 15)) // June 2026
    expect(currentFyOption()).toBe("2026-27")
  })

  it("returns the FY starting last year when the date is before April", () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 1, 15)) // February 2026
    expect(currentFyOption()).toBe("2025-26")
  })

  it("treats April itself as the start of the new FY", () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 3, 1)) // April 1, 2026
    expect(currentFyOption()).toBe("2026-27")
  })
})

describe("fyOptions", () => {
  it("returns 6 consecutive FYs ending at the current one", () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 5, 15)) // June 2026 -> FY2026-27
    const options = fyOptions()
    vi.useRealTimers()

    expect(options).toEqual(["2026-27", "2025-26", "2024-25", "2023-24", "2022-23", "2021-22"])
  })
})
