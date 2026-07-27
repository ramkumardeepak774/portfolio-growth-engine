import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { watchlistService } from "@/services/watchlist"
import type { AddWatchlistRequest } from "@/types"

export const WATCHLIST_KEY = ["watchlist"] as const

export function useWatchlist() {
  return useQuery({
    queryKey: WATCHLIST_KEY,
    queryFn: watchlistService.getWatchlist,
    staleTime: 2 * 60 * 1000, // 2 min — prices are live, shorter than holdings' 5 min
    retry: 1,
  })
}

export function useAddToWatchlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AddWatchlistRequest) => watchlistService.addToWatchlist(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: WATCHLIST_KEY }),
  })
}

export function useRemoveFromWatchlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (symbol: string) => watchlistService.removeFromWatchlist(symbol),
    onSuccess: () => qc.invalidateQueries({ queryKey: WATCHLIST_KEY }),
  })
}
