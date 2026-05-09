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

export interface MedalEntry {
  code: string
  name: string
  count: number
  latest_date?: string | null
  best_rank?: number | null
}

export interface StockDetail {
  ticker: string
  name: string
  theme?: string | null
  persona?: string | null
  medal_count: Record<string, number>
  medal_history: MedalEntry[]
  tier_distribution: Record<string, number>
  last_close?: number | null
  last_pct_change?: number | null
  recent_30d?: Array<{ date: string; close: number; pct_change?: number; tier?: string }>
}

export interface PortfolioPosition {
  ticker: string
  shares: number
  avg_cost: number
  last_close: number
  market_value: number
  unrealized_pnl: number
  today_pnl: number
  today_pct: number
  tier_today: string | null
  lottery?: boolean
}

export interface RaceEntry {
  ticker: string
  value: number
  rank: number
}

export interface RaceFrame {
  date: string
  entries: RaceEntry[]
}

export interface RaceResponse {
  metric: string
  period: string
  frames: RaceFrame[]
}

export interface PortfolioToday {
  as_of: string
  total_market_value: number
  total_unrealized_pnl: number
  today_pnl: number
  pillar?: { ticker: string; contribution: number } | null
  traitor?: { ticker: string; contribution: number } | null
  highlights?: Record<string, { ticker: string; contribution: number } | null>
  positions: PortfolioPosition[]
}

export interface LeaderboardEntry {
  ticker: string
  persona: string | null
  gold: number
  silver: number
  bronze: number
  total: number
}

export interface AwardTopEntry {
  ticker: string
  total_wins: number
  gold: number
  silver: number
  bronze: number
}