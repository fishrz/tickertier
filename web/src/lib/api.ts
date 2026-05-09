import axios from 'axios'
import type { AwardsTodayResponse, HealthResponse, PortfolioToday, StockDetail, LeaderboardEntry, AwardTopEntry } from '@/types'

export const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

export interface StatsResponse {
  universe: number
  awards: number
  medals_awarded: number
  data_from: string | null
  data_to: string | null
}

export async function getStats(): Promise<StatsResponse> {
  const r = await api.get('/stats')
  return r.data
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get('/health')
  return data
}

export async function getAwardsToday(): Promise<AwardsTodayResponse> {
  const { data } = await api.get('/awards/today')
  return data
}

export async function getTodayTiers(): Promise<{ date: string; members: Record<string, string[]> }> {
  const { data } = await api.get('/awards/today/tiers')
  return data
}

export async function getAwardsPeriod(period: string, key: string) {
  const { data } = await api.get(`/awards/period/${period}/${key}`)
  return data
}

export async function getLeaderboard(
  params: { window?: string; granularity?: string; limit?: number } = {},
): Promise<LeaderboardEntry[]> {
  const { window = 'all', granularity = 'ALL', limit = 20 } = params
  const r = await api.get<LeaderboardEntry[]>('/awards/leaderboard', {
    params: { window, granularity, limit },
  })
  return r.data
}

export async function getAwardTopByCode(code: string, n = 3): Promise<AwardTopEntry[]> {
  const { data } = await api.get(`/awards/by-code/${code}/top`, { params: { n } })
  return data
}

export interface RelatedStock {
  ticker: string
  persona: string | null
  theme: string
}
export interface RelatedResponse {
  ticker: string
  self_persona: string | null
  self_theme: string
  same_persona: RelatedStock[]
  same_theme: RelatedStock[]
}

export async function getStockRelated(ticker: string, limit = 8): Promise<RelatedResponse> {
  const { data } = await api.get(`/stocks/${ticker}/related`, { params: { limit } })
  return data
}

export async function getStock(ticker: string): Promise<StockDetail> {
  const { data } = await api.get(`/stocks/${ticker}`)
  return data
}

export async function getStockMedals(ticker: string, period = 'Y') {
  const { data } = await api.get(`/stocks/${ticker}/medals`, { params: { period } })
  return data
}

export async function getRace(
  metric = 'cum_return',
  options: { from?: string; to?: string } = {}
) {
  const params: Record<string, string> = { metric }
  if (options.from) params.from = options.from
  if (options.to) params.to = options.to
  const { data } = await api.get('/race', { params })
  return data
}

export async function getPortfolioToday(): Promise<PortfolioToday> {
  const { data } = await api.get('/portfolio/today')
  return data
}

// ── Award metadata (for info modal) ────────────────────────────
export interface AwardMeta {
  code: string
  name: string
  desc: string
  category: string
  unit: string
  criterion: string
  formula: string
}

export interface AwardMetaResponse {
  meta: AwardMeta
  top_holders: { ticker: string; wins: number }[]
  total_awarded: number
  last_winner: { period_key: string; ticker: string; value: number | null } | null
}

export async function getAwardMeta(code: string): Promise<AwardMetaResponse> {
  const { data } = await api.get(`/awards/meta/${code}`)
  return data
}
