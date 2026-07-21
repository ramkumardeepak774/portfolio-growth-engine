import api from "@/lib/api"
import type {
  AddTransactionRequest,
  AllocationData,
  GoalProgress,
  HoldingRow,
  PortfolioGrowth,
  PortfolioSummary,
  RebalanceAction,
} from "@/types"

export const portfolioService = {
  getSummary: async (): Promise<PortfolioSummary> => {
    const { data } = await api.get<PortfolioSummary>("/api/portfolio/summary")
    return data
  },

  getHoldings: async (): Promise<HoldingRow[]> => {
    const { data } = await api.get<HoldingRow[]>("/api/portfolio/holdings")
    return data
  },

  getAllocation: async (): Promise<AllocationData> => {
    const { data } = await api.get<AllocationData>("/api/portfolio/allocation")
    return data
  },

  getRebalance: async (): Promise<RebalanceAction[]> => {
    const { data } = await api.get<RebalanceAction[]>("/api/portfolio/rebalance")
    return data
  },

  getGoals: async (): Promise<GoalProgress[]> => {
    const { data } = await api.get<GoalProgress[]>("/api/portfolio/goals")
    return data
  },

  getGrowth: async (period = "1y"): Promise<PortfolioGrowth> => {
    const { data } = await api.get<PortfolioGrowth>("/api/portfolio/growth", { params: { period } })
    return data
  },

  addTransaction: async (payload: AddTransactionRequest): Promise<{ status: string }> => {
    const { data } = await api.post<{ status: string }>("/api/portfolio/transactions", payload)
    return data
  },
}
