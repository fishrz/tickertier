import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Data contract:
// - ratio / percent-like market metrics are stored as fractions (0.0965 = 9.65%).
// - portfolio percentage awards are also fractions after 2026-05-12 fixes.
// - vol_ratio_20 is a multiplier (3.94 = 3.94× average volume), NOT a percent.
// Never infer units from numeric magnitude; award code decides the formatter.
const PERCENT_AWARDS = new Set([
  'daily_king', 'daily_clown',
  'champion', 'stock_king', 'crap',
  'tank', 'comeback', 'oscar', 'roller_coaster',
  'rocket', 'crash', 'volatile', 'high_dive', 'gap',
  'earnings_god', 'earnings_clown',
  'big_position', 'buy_low',
])

const AMPLITUDE_AWARDS = new Set(['npc_god', 'gambler'])
const MULTIPLE_AWARDS = new Set(['pump_army'])
const AMOUNT_AWARDS = new Set(['pillar', 'traitor', 'cash_king', 'tear_jerker'])
const COUNT_AWARDS = new Set(['workhorse', 'silver_curse'])
const SCORE_AWARDS = new Set(['steady_grind', 'reverse_idx'])

export function formatMetric(code: string, value: number): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  if (PERCENT_AWARDS.has(code) || AMPLITUDE_AWARDS.has(code)) {
    return formatPercent(value)
  }
  if (MULTIPLE_AWARDS.has(code)) {
    return `${value.toFixed(value >= 10 ? 1 : 2)}× 均量`
  }
  if (COUNT_AWARDS.has(code)) {
    return `${Math.round(value)} 次`
  }
  if (AMOUNT_AWARDS.has(code)) {
    return formatAmount(value)
  }
  if (SCORE_AWARDS.has(code)) {
    return value.toFixed(3)
  }
  return value.toFixed(2)
}

export function formatPercent(v: number): string {
  // Convention: ALL percent inputs are fractions (0.0965 = 9.65%, 1.17 = 117%).
  // Never gate on Math.abs(v); that breaks ≥100% returns.
  const scaled = v * 100
  const sign = scaled > 0 ? '+' : ''
  return `${sign}${scaled.toFixed(2)}%`
}

export function formatAmount(v: number): string {
  const sign = v < 0 ? '-' : ''
  const abs = Math.abs(v)
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(1)}K`
  return `${sign}$${abs.toFixed(0)}`
}

// Magazine-style numerals (球员卡 / 排名感), not emoji medals
export const MEDALS = ['①', '②', '③'] as const

// Awards where being on the list is "bad" (color metric red regardless of sign)
const NEGATIVE_AWARDS = new Set(['tank', 'crash', 'high_dive', 'daily_clown', 'traitor', 'silver_curse', 'crap'])
// Awards where being on the list is "good" (color metric green)
const POSITIVE_AWARDS = new Set([
  'daily_king', 'champion', 'stock_king', 'comeback', 'rocket', 'pillar',
  'cash_king', 'buy_low', 'big_position', 'earnings_god', 'pump_army',
])

export function metricTone(code: string, value: number): 'pos' | 'neg' | 'neutral' {
  if (NEGATIVE_AWARDS.has(code)) return 'neg'
  if (POSITIVE_AWARDS.has(code)) return 'pos'
  if (value > 0) return 'pos'
  if (value < 0) return 'neg'
  return 'neutral'
}
