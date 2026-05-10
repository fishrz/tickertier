import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getPortfolioToday } from '@/lib/api'
import { formatPercent } from '@/lib/format'
import { Hero } from '@/components/Hero'
import { TierBar } from '@/components/TierBar'
import { StockChip } from '@/components/StockChip'
import { TierBadge } from '@/components/TierBadge'
import type { PortfolioPosition, PortfolioToday as PortfolioTodayType } from '@/types'

// —— Helpers ——
function pnlCls(v: number): string {
  if (v > 0) return 'text-pos'
  if (v < 0) return 'text-neg'
  return 'text-ink'
}

function fmtDollar(v: number): string {
  const sign = v < 0 ? '-' : v > 0 ? '+' : ''
  const abs = Math.abs(v)
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(1)}K`
  return `${sign}$${abs.toFixed(0)}`
}

function fmtBigDollar(v: number): string {
  const abs = Math.abs(v)
  if (abs >= 1_000_000) return `$${(abs / 1_000_000).toFixed(2)}M`
  if (abs >= 1_000) return `$${(abs / 1_000).toFixed(1)}K`
  return `$${abs.toFixed(0)}`
}

// —— Award highlight cards ——
type AwardKind = 'pillar' | 'traitor' | 'cash_king' | 'tear_jerker' | 'big_position' | 'buy_low'

interface AwardCardCfg {
  kind: AwardKind
  emoji: string
  label: string
  sub: string
  tip: string
  unit: 'amount' | 'pct'
  positive: 'good' | 'bad' | 'neutral' // color class for the metric
  accent: string // top border color class
}

const AWARD_CARDS: AwardCardCfg[] = [
  { kind: 'pillar',       emoji: '💰', label: '顶梁柱',     sub: '今日最大正贡献',
    tip: '今日 pnl = shares × Δprice，最正的那只',
    unit: 'amount', positive: 'good', accent: 'border-t-gold' },
  { kind: 'traitor',      emoji: '🩸', label: '拖后腿',     sub: '今日最大负贡献',
    tip: '今日 pnl 最负的那只，建议清仓谢罪',
    unit: 'amount', positive: 'bad',  accent: 'border-t-neg' },
  { kind: 'cash_king',    emoji: '💸', label: '钞能力之王', sub: '累计浮盈最厚',
    tip: '(last_close − avg_cost) × shares 最大的持仓',
    unit: 'amount', positive: 'good', accent: 'border-t-gold' },
  { kind: 'tear_jerker',  emoji: '😭', label: '我的眼泪',   sub: '累计浮亏最深',
    tip: '套牢冠军：(last_close − avg_cost) × shares 最负',
    unit: 'amount', positive: 'bad',  accent: 'border-t-neg' },
  { kind: 'big_position', emoji: '👑', label: '仓位之王',   sub: '账户市值占比最高',
    tip: 'shares × last_close / 总市值，谁是压舱石',
    unit: 'pct',    positive: 'neutral', accent: 'border-t-ink' },
  { kind: 'buy_low',      emoji: '🧠', label: '人间清醒',   sub: '相对成本折扣最大',
    tip: '(last_close − avg_cost) / avg_cost 最高，买在脚踝上',
    unit: 'pct',    positive: 'good', accent: 'border-t-gold' },
]

function HighlightCard({
  cfg,
  data,
}: {
  cfg: AwardCardCfg
  data: { ticker: string; contribution: number } | null | undefined
}) {
  const numCls =
    cfg.positive === 'good' ? 'text-pos'
    : cfg.positive === 'bad' ? 'text-neg'
    : 'text-ink'
  const valueText = data
    ? cfg.unit === 'amount'
      ? fmtDollar(data.contribution)
      : `${data.contribution.toFixed(1)}%`
    : '—'
  return (
    <article
      className={`border border-ink border-t-4 ${cfg.accent} px-5 pt-5 pb-4 bg-paper`}
      title={cfg.tip}
    >
      <div className="flex items-center gap-1.5 mb-1.5">
        <span className="text-[16px]">{cfg.emoji}</span>
        <div className="kicker">— {cfg.label} —</div>
      </div>
      <div className="font-serif font-black text-[28px] leading-none tracking-[-0.02em] mb-1.5">
        {data
          ? <StockChip ticker={data.ticker} className="text-[28px] px-2 py-0.5" />
          : <span className="text-mute">—</span>}
      </div>
      <div className="text-[10px] text-mute mb-2.5 border-b border-dotted border-mute inline-block cursor-help"
           title={cfg.tip}>
        {cfg.sub} ⓘ
      </div>
      <div className={`font-mono font-bold text-[22px] tabular-nums ${data ? numCls : 'text-mute'}`}>
        {valueText}
      </div>
    </article>
  )
}

// —— Holdings table row ——
function PositionRow({ pos, totalMv }: { pos: PortfolioPosition; totalMv: number }) {
  const weight = totalMv > 0 ? (pos.market_value / totalMv) * 100 : 0
  return (
    <tr className={`border-b border-paper-2 hover:bg-paper-2 transition-colors ${pos.lottery ? 'opacity-60' : ''}`}>
      <td className="py-3 pr-4 font-mono font-bold">
        <Link to={`/stock/${pos.ticker}`} className="hover:text-gold-dim">{pos.ticker}</Link>
        {pos.lottery && (
          <span
            className="ml-2 inline-block align-middle font-mono text-[9px] uppercase tracking-[0.1em] px-1.5 py-[1px] border border-mute text-mute rounded-sm"
            title="彩票仓 — 占比 <0.5%，仅展示，不参与持仓奖项评选"
          >
            🎟 LOTTO
          </span>
        )}
      </td>
      <td className="py-3 pr-4">{pos.tier_today ? <TierBadge tier={pos.tier_today} /> : '—'}</td>
      <td className="py-3 pr-4 font-mono tabular-nums text-right">{pos.shares.toLocaleString()}</td>
      <td className="py-3 pr-4 font-mono tabular-nums text-right">${pos.avg_cost.toFixed(2)}</td>
      <td className="py-3 pr-4 font-mono tabular-nums text-right">${pos.last_close.toFixed(2)}</td>
      <td className={`py-3 pr-4 font-mono tabular-nums text-right ${pnlCls(pos.today_pct)}`}>
        {formatPercent(pos.today_pct)}
      </td>
      <td className={`py-3 pr-4 font-mono tabular-nums text-right ${pnlCls(pos.today_pnl)}`}>
        {fmtDollar(pos.today_pnl)}
      </td>
      <td className="py-3 font-mono tabular-nums text-right">{weight.toFixed(2)}%</td>
    </tr>
  )
}

// —— Sortable holdings table ——
type SortKey =
  | 'ticker' | 'tier' | 'shares' | 'avg_cost' | 'last_close'
  | 'today_pct' | 'today_pnl' | 'weight'
type SortDir = 'asc' | 'desc'

// Tier ordering for sort: best -> worst (higher rank index = better)
const TIER_RANK: Record<string, number> = {
  '🔥 夯死了': 6,
  '👑 顶级': 5,
  '💪 人上人': 4,
  '😐 NPC': 3,
  '💩 拉完了': 2,
  '☠️ 答辩': 1,
}

function HoldingsTable({
  positions, totalMv,
}: { positions: PortfolioPosition[]; totalMv: number }) {
  // Default: tier desc (best tier on top)
  const [sortKey, setSortKey] = useState<SortKey>('tier')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const sorted = useMemo(() => {
    const get = (p: PortfolioPosition): number | string => {
      switch (sortKey) {
        case 'ticker':     return p.ticker
        case 'tier':       return TIER_RANK[p.tier_today || ''] ?? 0
        case 'shares':     return p.shares
        case 'avg_cost':   return p.avg_cost
        case 'last_close': return p.last_close
        case 'today_pct':  return p.today_pct
        case 'today_pnl':  return p.today_pnl
        case 'weight':     return totalMv > 0 ? p.market_value / totalMv : 0
      }
    }
    const cmp = (a: PortfolioPosition, b: PortfolioPosition) => {
      // Lottery rows always pinned to bottom
      if (!!a.lottery !== !!b.lottery) return a.lottery ? 1 : -1
      const va = get(a), vb = get(b)
      let r = 0
      if (typeof va === 'string' && typeof vb === 'string') {
        r = va.localeCompare(vb)
      } else {
        r = (va as number) - (vb as number)
      }
      return sortDir === 'asc' ? r : -r
    }
    return [...positions].sort(cmp)
  }, [positions, totalMv, sortKey, sortDir])

  const onSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      // Numeric cols default to desc (most useful first); ticker defaults asc
      setSortDir(key === 'ticker' ? 'asc' : 'desc')
    }
  }

  const arrow = (key: SortKey) =>
    sortKey === key ? (sortDir === 'asc' ? '▲' : '▼') : '↕'

  const Th = ({ k, label, align = 'left' }: { k: SortKey; label: string; align?: 'left' | 'right' }) => (
    <th
      className={
        'py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute select-none cursor-pointer hover:text-ink transition-colors ' +
        (align === 'right' ? 'text-right' : '')
      }
      onClick={() => onSort(k)}
      title={`按 ${label} 排序`}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        <span className={'text-[9px] ' + (sortKey === k ? 'text-gold' : 'text-mute opacity-50')}>
          {arrow(k)}
        </span>
      </span>
    </th>
  )

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-[13px]">
        <thead>
          <tr className="border-b-[2px] border-ink">
            <Th k="ticker" label="Ticker" />
            <Th k="tier" label="Tier" />
            <Th k="shares" label="Shares" align="right" />
            <Th k="avg_cost" label="Avg Cost" align="right" />
            <Th k="last_close" label="Close" align="right" />
            <Th k="today_pct" label="Today%" align="right" />
            <Th k="today_pnl" label="Today $" align="right" />
            <Th k="weight" label="Wt%" align="right" />
          </tr>
        </thead>
        <tbody>
          {sorted.map((pos) => (
            <PositionRow key={pos.ticker} pos={pos} totalMv={totalMv} />
          ))}
        </tbody>
      </table>
    </div>
  )
}
export default function Portfolio() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['portfolio', 'today'],
    queryFn: getPortfolioToday,
  })

  if (isLoading) {
    return <div className="py-32 text-center kicker">— LOADING —</div>
  }
  if (isError || !data) {
    return (
      <div className="py-32 text-center text-neg font-mono text-sm">
        加载失败: {(error as Error)?.message || '未知错误'}
      </div>
    )
  }

  const d = data as PortfolioTodayType
  // Build tier distribution from held positions only
  const heldDistribution: Record<string, number> = {}
  for (const p of d.positions) {
    if (p.tier_today) {
      heldDistribution[p.tier_today] = (heldDistribution[p.tier_today] || 0) + 1
    }
  }

  const totalToday = d.today_pnl

  return (
    <>
      <Hero
        title={
          <>
            <span className="block">持仓</span>
            <span className="block">
              <em className="not-italic font-bold text-gold-dim italic">战报</em>
            </span>
          </>
        }
        bigStat={fmtBigDollar(d.total_market_value)}
        bigStatLabel="总市值"
        bottomLine={
          <span className={pnlCls(totalToday)}>
            今日 {totalToday >= 0 ? '+' : ''}{fmtDollar(totalToday)}
          </span>
        }
      />

      {/* Award highlight cards — 6 awards in a responsive grid */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-0 border-b border-ink [&>*+*]:border-l-0 sm:[&>*:nth-child(2n+1)]:border-l-0 lg:[&>*:nth-child(3n+1)]:border-l-0">
        {AWARD_CARDS.map((cfg) => (
          <HighlightCard
            key={cfg.kind}
            cfg={cfg}
            data={d.highlights?.[cfg.kind] ?? (cfg.kind === 'pillar' ? d.pillar : cfg.kind === 'traitor' ? d.traitor : null)}
          />
        ))}
      </section>

      {/* Holdings table */}
      <section className="pt-10 pb-4">
        <div className="kicker mb-2">— 完整持仓 —</div>
        <div className="flex items-end gap-4 mb-2">
          <h2 className="font-serif font-black text-[48px] leading-none tracking-[-0.03em]">
            持仓列表
          </h2>
          <Link
            to="/portfolio/edit"
            className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute hover:text-gold transition-colors border-b border-dotted border-mute pb-0.5 mb-1"
          >
            编辑持仓
          </Link>
        </div>
        <p className="text-sm text-mute mb-8 max-w-[600px] leading-relaxed">
          默认按 Tier 排序，点表头切换排序字段（再点一次反向）。点 ticker 看个股履历。彩票仓固定置底。
        </p>

        <HoldingsTable positions={d.positions} totalMv={d.total_market_value} />
      </section>

      {/* Tier distribution — held stocks only */}
      <section className="pb-12">
        <TierBar distribution={heldDistribution} label="持仓 TIER 分布" />
      </section>
    </>
  )
}