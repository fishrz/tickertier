import axios from 'axios'
import type { AwardsTodayResponse, HealthResponse, PortfolioToday, StockDetail, LeaderboardEntry, AwardTopEntry } from '@/types'

export const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

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

export async function getLeaderboard(period = 'D', limit = 20): Promise<LeaderboardEntry[]> {
  const { data } = await api.get('/awards/leaderboard', { params: { period, limit } })
  return data
}

export async function getAwardTopByCode(code: string, n = 3): Promise<AwardTopEntry[]> {
  const { data } = await api.get(`/awards/by-code/${code}/top`, { params: { n } })
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

export async function getRace(metric = 'cum_return', period = 'Y') {
  const { data } = await api.get('/race', { params: { metric, period } })
  return data
}

export async function getPortfolioToday(): Promise<PortfolioToday> {
  const { data } = await api.get('/portfolio/today')
  return data
}