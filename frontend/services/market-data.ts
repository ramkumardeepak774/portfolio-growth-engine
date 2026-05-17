import api from "@/lib/api"
import type { Fundamentals, JournalEntry, CreateJournalEntryRequest, PricePoint } from "@/types"

type Period = "1mo" | "3mo" | "6mo" | "1y" | "2y" | "5y" | "max"

export const marketDataService = {
  getPrices: async (symbol: string, period: Period = "1y"): Promise<PricePoint[]> => {
    const { data } = await api.get<PricePoint[]>(`/api/data/prices/${symbol}`, {
      params: { period },
    })
    return data
  },

  getFundamentals: async (symbol: string): Promise<Fundamentals> => {
    const { data } = await api.get<Fundamentals>(`/api/data/fundamentals/${symbol}`)
    return data
  },
}

export const journalService = {
  getEntries: async (params?: { symbol?: string; action?: string }): Promise<JournalEntry[]> => {
    const { data } = await api.get<{ entries: JournalEntry[] }>("/api/journal/entries", { params })
    return data.entries ?? data as unknown as JournalEntry[]
  },

  createEntry: async (payload: CreateJournalEntryRequest): Promise<{ id: string }> => {
    const { data } = await api.post<{ id: string; status: string }>("/api/journal/entry", payload)
    return data
  },

  getEntry: async (id: string): Promise<JournalEntry> => {
    const { data } = await api.get<JournalEntry>(`/api/journal/entries/${id}`)
    return data
  },

  reviewEntry: async (
    id: string,
    payload: {
      outcome: string
      what_went_right?: string
      what_went_wrong?: string
      bias_identified?: string
      lesson_learned?: string
      rating?: number
    },
  ): Promise<void> => {
    await api.post(`/api/journal/review/${id}`, payload)
  },
}
