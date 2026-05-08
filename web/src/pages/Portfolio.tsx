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

// —— Pillar / Traitor big cards ——
function HighlightCard({
  kind,
  data,
}: {
  kind: 'pillar' | 'traitor'
  data: { ticker: string; contribution: number } | null | undefined
}) {
  const isPillar = kind === 'pillar'
  const label = isPillar ? '顶梁柱' : '拖后腿'
  const sub = isPillar ? '今日最大正贡献' : '今日最大负贡献'
  const borderCls = isPillar ? 'border-t-4 border-t-gold' : 'border-t-4 border-t-neg'
  const numCls = isPillar ? 'text-pos' : 'text-neg'

  return (
    <article className={`flex-1 border border-ink ${borderCls} px-7 pt-7 pb-6`}>
      <div className="kicker mb-2.5">— {label} —</div>
      <div className="font-serif font-black text-[40px] leading-none tracking-[-0.02em] mb-2">
        {data ? <StockChip ticker={data.ticker} className="text-[40px] px-3 py-1" /> : <span className="text-mute">—</span>}
      </div>
      <div className="text-[12px] text-mute mb-4">{sub}</div>
      {data ? (
        <div className={`font-mono font-bold text-[28px] tabular-nums ${numCls}`}>
          {fmtDollar(data.contribution)}
        </div>
      ) : (
        <div className="font-mono text-[28px] text-mute">—</div>
      )}
    </article>
  )
}

// —— Holdings table row ——
function PositionRow({ pos, totalMv }: { pos: PortfolioPosition; totalMv: number }) {
  const weight = totalMv > 0 ? (pos.market_value / totalMv) * 100 : 0
  return (
    <tr className="border-b border-paper-2 hover:bg-paper-2 transition-colors">
      <td className="py-3 pr-4 font-mono font-bold">
        <Link to={`/stock/${pos.ticker}`} className="hover:text-gold-dim">{pos.ticker}</Link>
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
      <td className="py-3 font-mono tabular-nums text-right">{weight.toFixed(1)}%</td>
    </tr>
  )
}

// —— Main page ——
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
  // Sort positions by contribution = shares * today_pct (descending)
  const sorted = [...d.positions].sort(
    (a, b) => (b.shares * b.today_pct) - (a.shares * a.today_pct)
  )

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

      {/* Pillar & Traitor cards */}
      <section className="flex flex-col md:flex-row gap-0 border-b border-ink">
        <HighlightCard kind="pillar" data={d.pillar} />
        <HighlightCard kind="traitor" data={d.traitor} />
      </section>

      {/* Holdings table */}
      <section className="pt-10 pb-4">
        <div className="kicker mb-2">— 完整持仓 —</div>
        <h2 className="font-serif font-black text-[48px] leading-none tracking-[-0.03em] mb-2">
          持仓列表
        </h2>
        <p className="text-sm text-mute mb-8 max-w-[600px] leading-relaxed">
          按贡献度排序（shares × today%）。点 ticker 看个股履历。
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b-[2px] border-ink">
                <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute">Ticker</th>
                <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute">Tier</th>
                <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute text-right">Shares</th>
                <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute text-right">Avg Cost</th>
                <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute text-right">Close</th>
                <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute text-right">Today%</th>
                <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute text-right">Today $</th>
                <th className="py-3 font-mono text-[11px] uppercase tracking-[0.15em] text-mute text-right">Wt%</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((pos) => (
                <PositionRow key={pos.ticker} pos={pos} totalMv={d.total_market_value} />
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Tier distribution — held stocks only */}
      <section className="pb-12">
        <TierBar distribution={heldDistribution} />
      </section>
    </>
  )
}