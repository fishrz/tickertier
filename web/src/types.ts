export type TierName =
  | '🔥 夯死了'
  | '👑 顶级'
  | '💪 人上人'
  | '😐 NPC'
  | '💩 拉完了'
  | '☠️ 答辩'

export interface Winner {
  rank: number
  ticker: string
  metric: number
  meta?: Record<string, unknown> | null
}

export interface AwardGroup {
  code: string
  name: string
  description: string
  winners: Winner[]
}

export interface AwardsTodayResponse {
  date: string
  awards: AwardGroup[]
  tier_distribution: Record<string, number>
}

export interface HealthResponse {
  status: string
  db_path: string
  as_of: string
}

export interface StockDetail {
  ticker: string
  name: string
  theme?: string | null
  persona?: string | null
  medal_count: number
  tier_distribution: Record<string, number>
  last_close?: number | null
  last_pct_change?: number | null
  recent_30d?: Array<{ date: string; close: number; pct_change?: number }>
}

export interface PortfolioPosition {
  ticker: string
  name?: string
  shares: number
  market_value: number
  unrealized_pnl: number
  today_pnl: number
}

export interface PortfolioToday {
  as_of: string
  total_market_value: number
  total_unrealized_pnl: number
  today_pnl: number
  pillar?: { ticker: string; pnl: number } | null
  traitor?: { ticker: string; pnl: number } | null
  positions: PortfolioPosition[]
}
