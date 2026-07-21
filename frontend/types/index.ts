// ─── Portfolio Types ──────────────────────────────────────────────────────────

export interface PortfolioSummary {
  total_invested: number
  total_value: number
  total_pnl: number
  total_pnl_pct: number
  cagr: number
  xirr: number | null
  holdings_count: number
}

export interface HoldingRow {
  symbol: string
  name: string
  asset_class: string
  sector: string | null
  quantity: number
  invested_amount: number
  current_value: number
  current_price: number | null
  pnl: number
  pnl_percent: number
  weight_pct?: number
  first_investment_date?: string
}

export interface AllocationData {
  by_asset_class: Record<string, number>
  by_sector: Record<string, number>
  concentration: {
    top3_pct?: number
    top5_pct?: number
    hhi?: number
  }
  current_buckets: Record<string, number>
}

export interface RebalanceAction {
  bucket: string
  current_pct: number
  target_pct: number
  diff_pct: number
  action: string
  amount: number
}

export interface GoalProgress {
  name: string
  target_multiplier: number
  target_years: number
  current_value: number
  target_value: number
  actual_cagr: number
  required_cagr: number
  required_cagr_from_now: number
  on_track: boolean
  years_remaining: number
  completion_pct: number
}

export interface PortfolioGrowthPoint {
  date: string
  value: number
}

export interface PortfolioGrowth {
  period: string
  series: PortfolioGrowthPoint[]
}

// ─── Market Data Types ────────────────────────────────────────────────────────

export interface PricePoint {
  Date: string
  Open: number
  High: number
  Low: number
  Close: number
  Volume: number
}

export interface Fundamentals {
  symbol: string
  name?: string
  sector?: string
  industry?: string
  market_cap?: number
  pe_ratio?: number
  pb_ratio?: number
  dividend_yield?: number
  roe?: number
  debt_to_equity?: number
  revenue_growth?: number
  earnings_growth?: number
}

// ─── Journal Types ────────────────────────────────────────────────────────────

export type JournalAction = "entry" | "exit" | "add" | "trim" | "hold" | "watchlist"
export type Conviction = "very_high" | "high" | "medium" | "low" | "speculative"

export interface JournalEntry {
  id: string
  symbol: string
  action: JournalAction
  why: string
  thesis: string
  assumptions: string[]
  expected_catalyst: string
  risk_factors: string[]
  invalidation_conditions: string[]
  time_horizon: string
  conviction: Conviction
  quantity: number
  price: number
  position_size_pct: number
  tags: string[]
  created_at: string
  reviewed: boolean
  rating?: number
  outcome?: string
  what_went_right?: string
  what_went_wrong?: string
  bias_identified?: string
  lesson_learned?: string
}

export interface CreateJournalEntryRequest {
  symbol: string
  action: JournalAction
  why: string
  thesis?: string
  assumptions?: string[]
  expected_catalyst?: string
  risk_factors?: string[]
  invalidation_conditions?: string[]
  time_horizon?: string
  conviction?: Conviction
  quantity?: number
  price?: number
  position_size_pct?: number
  tags?: string[]
}

// ─── Analytics Types (computed client-side) ───────────────────────────────────

export interface PortfolioAnalytics {
  cagr: number
  xirr: number | null
  alpha: number | null
  beta: number | null
  sharpe: number | null
  volatility: number | null
  max_drawdown: number | null
  benchmark_return: number | null
}

export interface ChartDataPoint {
  date: string
  value: number
  benchmark?: number
}

// ─── Insights ────────────────────────────────────────────────────────────────

export interface Insight {
  type: "warning" | "info" | "success"
  title: string
  description: string
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string
  email: string
  name?: string
}

export interface AuthState {
  user: AuthUser | null
  token: string | null
  isLoading: boolean
}
