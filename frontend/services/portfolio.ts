import api from "@/lib/api"
import type {
  AllocationData,
  GoalProgress,
  HoldingRow,
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
}
