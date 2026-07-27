import api from "@/lib/api"
import type { AddWatchlistRequest, WatchlistItem } from "@/types"

export const watchlistService = {
  getWatchlist: async (): Promise<WatchlistItem[]> => {
    const { data } = await api.get<WatchlistItem[]>("/api/watchlist")
    return data
  },

  addToWatchlist: async (payload: AddWatchlistRequest): Promise<{ status: string }> => {
    const { data } = await api.post<{ status: string }>("/api/watchlist", payload)
    return data
  },

  removeFromWatchlist: async (symbol: string): Promise<{ status: string }> => {
    const { data } = await api.delete<{ status: string }>(`/api/watchlist/${symbol}`)
    return data
  },
}
