import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { portfolioService } from "@/services/portfolio"
import { marketDataService } from "@/services/market-data"
import type { AddTransactionRequest } from "@/types"

function invalidatePortfolioQueries(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: PORTFOLIO_KEYS.summary })
  qc.invalidateQueries({ queryKey: PORTFOLIO_KEYS.holdings })
  qc.invalidateQueries({ queryKey: PORTFOLIO_KEYS.allocation })
  qc.invalidateQueries({ queryKey: PORTFOLIO_KEYS.rebalance })
  qc.invalidateQueries({ queryKey: ["portfolio", "growth"] })
}

export const PORTFOLIO_KEYS = {
  summary: ["portfolio", "summary"] as const,
  holdings: ["portfolio", "holdings"] as const,
  allocation: ["portfolio", "allocation"] as const,
  rebalance: ["portfolio", "rebalance"] as const,
  goals: ["portfolio", "goals"] as const,
  growth: (period: string) => ["portfolio", "growth", period] as const,
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

export function usePortfolioGrowth(period = "1y") {
  return useQuery({
    queryKey: PORTFOLIO_KEYS.growth(period),
    queryFn: () => portfolioService.getGrowth(period),
    staleTime: 60 * 60 * 1000, // 1 hour — historical data doesn't change often
    retry: 1,
  })
}

export function useAddTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AddTransactionRequest) => portfolioService.addTransaction(payload),
    onSuccess: () => invalidatePortfolioQueries(qc),
  })
}

/** dryRun=true previews without writing; dryRun=false commits and invalidates the portfolio queries. */
export function useImportCsv() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ file, dryRun }: { file: File; dryRun: boolean }) =>
      portfolioService.importCsv(file, dryRun),
    onSuccess: (_data, variables) => {
      if (!variables.dryRun) invalidatePortfolioQueries(qc)
    },
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
