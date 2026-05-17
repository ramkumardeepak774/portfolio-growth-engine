import { useQuery } from "@tanstack/react-query"
import { portfolioService } from "@/services/portfolio"
import { marketDataService } from "@/services/market-data"

export const PORTFOLIO_KEYS = {
  summary: ["portfolio", "summary"] as const,
  holdings: ["portfolio", "holdings"] as const,
  allocation: ["portfolio", "allocation"] as const,
  rebalance: ["portfolio", "rebalance"] as const,
  goals: ["portfolio", "goals"] as const,
  prices: (symbol: string, period: string) => ["market", "prices", symbol, period] as const,
  fundamentals: (symbol: string) => ["market", "fundamentals", symbol] as const,
}

export function usePortfolioSummary() {
  return useQuery({
    queryKey: PORTFOLIO_KEYS.summary,
    queryFn: portfolioService.getSummary,
    staleTime: 5 * 60 * 1000, // 5 min
    retry: 2,
  })
}

export function useHoldings() {
  return useQuery({
    queryKey: PORTFOLIO_KEYS.holdings,
    queryFn: portfolioService.getHoldings,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  })
}

export function useAllocation() {
  return useQuery({
    queryKey: PORTFOLIO_KEYS.allocation,
    queryFn: portfolioService.getAllocation,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  })
}

export function useRebalance() {
  return useQuery({
    queryKey: PORTFOLIO_KEYS.rebalance,
    queryFn: portfolioService.getRebalance,
    staleTime: 10 * 60 * 1000,
    retry: 2,
  })
}

export function useGoals() {
  return useQuery({
    queryKey: PORTFOLIO_KEYS.goals,
    queryFn: portfolioService.getGoals,
    staleTime: 10 * 60 * 1000,
    retry: 2,
  })
}

export function useStockPrices(symbol: string, period = "1y") {
  return useQuery({
    queryKey: PORTFOLIO_KEYS.prices(symbol, period),
    queryFn: () => marketDataService.getPrices(symbol, period as "1y"),
    enabled: Boolean(symbol),
    staleTime: 60 * 60 * 1000, // 1 hour — historical data doesn't change often
    retry: 1,
  })
}

export function useFundamentals(symbol: string) {
  return useQuery({
    queryKey: PORTFOLIO_KEYS.fundamentals(symbol),
    queryFn: () => marketDataService.getFundamentals(symbol),
    enabled: Boolean(symbol),
    staleTime: 60 * 60 * 1000,
    retry: 1,
  })
}
