import api from "@/lib/api"
import type {
  AddTransactionRequest,
  AllocationData,
  GoalProgress,
  HoldingRow,
  ImportCsvResponse,
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

  importCsv: async (file: File, dryRun: boolean): Promise<ImportCsvResponse> => {
    const form = new FormData()
    form.append("file", file)
    // Must unset (not override) the axios instance's default JSON
    // Content-Type — a literal "multipart/form-data" string lacks the
    // boundary parameter the server needs; letting axios set it itself
    // (from the FormData) gets that right.
    const { data } = await api.post<ImportCsvResponse>(
      "/api/portfolio/import/csv",
      form,
      { params: { dry_run: dryRun }, headers: { "Content-Type": undefined } },
    )
    return data
  },
}
