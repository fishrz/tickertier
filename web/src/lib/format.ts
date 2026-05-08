import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const PERCENT_AWARDS = new Set([
  'champion', 'tank', 'comeback', 'oscar', 'roller_coaster',
  'daily_clown', 'rocket', 'crash', 'volatile',
])
const AMOUNT_AWARDS = new Set(['pillar', 'traitor'])
const COUNT_AWARDS = new Set(['workhorse', 'silver_curse'])
const SCORE_AWARDS = new Set(['steady_grind', 'gambler', 'reverse_idx', 'npc_god'])

export function formatMetric(code: string, value: number): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  if (COUNT_AWARDS.has(code)) {
    return `${Math.round(value)} 次`
  }
  if (SCORE_AWARDS.has(code)) {
    return value.toFixed(3)
  }
  if (AMOUNT_AWARDS.has(code)) {
    return formatAmount(value)
  }
  if (PERCENT_AWARDS.has(code)) {
    return formatPercent(value)
  }
  // heuristic
  if (Math.abs(value) < 100) return formatPercent(value)
  if (Math.abs(value) > 10000) return formatAmount(value)
  return value.toFixed(2)
}

export function formatPercent(v: number): string {
  // API returns fractions for return metrics (0.0965 = 9.65%); also handle pre-scaled values
  const scaled = Math.abs(v) < 1 ? v * 100 : v
  const sign = scaled > 0 ? '+' : ''
  return `${sign}${scaled.toFixed(2)}%`
}

export function formatAmount(v: number): string {
  const sign = v < 0 ? '-' : ''
  const abs = Math.abs(v)
  if (abs >= 1_000_000) return `${sign}¥${(abs / 1_000_000).toFixed(1)}M`
  if (abs >= 1_000) return `${sign}¥${(abs / 1_000).toFixed(1)}K`
  return `${sign}¥${abs.toFixed(0)}`
}

// Magazine-style numerals (球员卡 / 排名感), not emoji medals
export const MEDALS = ['①', '②', '③'] as const

// Awards where being on the list is "bad" (color metric red regardless of sign)
const NEGATIVE_AWARDS = new Set(['tank', 'crash', 'high_dive', 'daily_clown', 'traitor', 'silver_curse'])
// Awards where being on the list is "good" (color metric green)
const POSITIVE_AWARDS = new Set(['champion', 'stock_king', 'comeback', 'rocket', 'pillar', 'earnings_god'])

export function metricTone(code: string, value: number): 'pos' | 'neg' | 'neutral' {
  if (NEGATIVE_AWARDS.has(code)) return 'neg'
  if (POSITIVE_AWARDS.has(code)) return 'pos'
  if (value > 0) return 'pos'
  if (value < 0) return 'neg'
  return 'neutral'
}
