import { Fragment } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'
import { getStock } from '@/lib/api'
import { formatPercent } from '@/lib/format'
import { PersonaPill } from '@/components/PersonaPill'
import { TierBadge } from '@/components/TierBadge'
import type { MedalEntry } from '@/types'
import type { StockDetail as StockDetailType } from '@/types'

// Gold end-point dot for sparkline — renders at the last data point
function GoldEndDot({ cx, cy }: { cx?: number; cy?: number }) {
  if (cx == null || cy == null) return null
  return (
    <circle cx={cx} cy={cy} r={3} fill="var(--gold)" stroke="var(--ink)" strokeWidth={1} />
  )
}

// Custom dot function: only render gold dot at the last data point
function sparklineDot(data: StockDetailType['recent_30d']) {
  return (props: { index?: number; cx?: number; cy?: number }) => {
    if (props.index === data!.length - 1) {
      return <GoldEndDot key="gold-end" cx={props.cx} cy={props.cy} />
    }
    return <Fragment key={props.index} />
  }
}

// Tier color mapping for the timeline strip
const TIER_COLOR: Record<string, string> = {
  '🔥 夯死了': 'var(--gold)',
  '👑 顶级': 'var(--gold-dim)',
  '💪 人上人': 'var(--ink)',
  '😐 NPC': 'var(--mute)',
  '💩 拉完了': 'rgba(10,10,10,.35)',
  '☠️ 答辩': 'var(--neg)',
}

export default function StockDetail() {
  const { ticker } = useParams<{ ticker: string }>()
  const q = useQuery({
    queryKey: ['stock', ticker],
    queryFn: () => getStock(ticker!),
    enabled: !!ticker,
  })

  if (q.isLoading) {
    return <div className="py-32 text-center kicker">— LOADING —</div>
  }
  if (q.isError || !q.data) {
    return (
      <div className="py-32 text-center text-neg font-mono text-sm">
        加载失败: {(q.error as Error)?.message || '未知错误'}
      </div>
    )
  }

  const d = q.data
  const pctTone = (d.last_pct_change ?? 0) > 0 ? 'pos' : (d.last_pct_change ?? 0) < 0 ? 'neg' : 'neutral'
  const pctCls = pctTone === 'pos' ? 'text-pos' : pctTone === 'neg' ? 'text-neg' : 'text-ink'

  return (
    <>
      {/* ── Headline ── */}
      <section className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-8 items-end py-12 border-b border-ink">
        <div>
          <div className="kicker mb-3">— 股票履历 —</div>
          <h1 className="font-serif font-black tracking-[-0.04em] leading-[0.92] text-[clamp(80px,9vw,120px)]">
            {d.ticker}
          </h1>
          <div className="flex items-baseline gap-4 mt-4">
            {d.last_close != null && (
              <span className="font-mono font-bold text-[28px] tabular-nums">
                ${d.last_close.toFixed(2)}
              </span>
            )}
            {d.last_pct_change != null && (
              <span className={`font-mono font-bold text-[20px] tabular-nums ${pctCls}`}>
                {formatPercent(d.last_pct_change)}
              </span>
            )}
            <PersonaPill persona={d.persona} />
          </div>
        </div>
        {/* Right side: total medals summary */}
        <div className="text-right font-mono text-[12px] uppercase tracking-[0.1em] text-mute leading-relaxed">
          <div className="font-serif text-[56px] text-ink font-black leading-none mb-2 tracking-[-0.02em]">
            {Object.values(d.medal_count).reduce((a, b) => a + b, 0)}
          </div>
          <div>枚奖牌</div>
          {d.medal_history.length > 0 && (
            <div className="mt-2 text-gold-dim">
              最佳: {d.medal_history[0].name}
            </div>
          )}
        </div>
      </section>

      {/* ── 30d sparkline ── */}
      {d.recent_30d && d.recent_30d.length > 1 && (
        <section className="py-8 border-b border-ink">
          <div className="kicker mb-4">— 30 日走势 —</div>
          <div className="h-[120px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={d.recent_30d} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke="var(--ink)"
                  strokeWidth={1}
                  dot={sparklineDot(d.recent_30d)}
                  activeDot={false}
                />
                <Tooltip
                  contentStyle={{ background: 'var(--paper)', border: '1px solid var(--ink)', fontSize: '12px', fontFamily: 'var(--mono)' }}
                  labelFormatter={(v) => `${v}`}
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  formatter={(value: any) => value != null ? [`$${Number(value).toFixed(2)}`, '收盘'] : ['—', '收盘']}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          {/* Date range footer */}
          <div className="flex items-baseline gap-2 mt-2 font-mono text-[11px] text-mute">
            <span>{d.recent_30d[0].date}</span>
            <span className="flex-1 border-b border-dotted border-mute/40" />
            <span>{d.recent_30d[d.recent_30d.length - 1].date}</span>
          </div>
        </section>
      )}

      {/* ── Medal Cabinet ── */}
      {d.medal_history.length > 0 && (
        <section className="py-10 border-b border-ink">
          <div className="kicker mb-4">— 奖牌柜 —</div>
          <h2 className="font-serif font-black text-[48px] leading-[1.05] tracking-[-0.02em] mb-6">
            获奖<em className="not-italic text-gold-dim italic font-bold">履历</em>
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-0">
            {d.medal_history.map((m: MedalEntry) => (
              <article
                key={m.code}
                className="border border-ink p-5 flex flex-col"
              >
                <div className="font-serif font-black text-[20px] leading-tight mb-1">
                  {m.name}
                </div>
                <div className="flex items-baseline gap-2 mt-auto pt-3">
                  <span className="font-mono font-bold text-[28px] text-gold tabular-nums leading-none">
                    {m.count}
                  </span>
                  <span className="font-mono text-[11px] text-mute uppercase tracking-wider">次</span>
                </div>
                {m.latest_date && (
                  <div className="font-mono text-[10px] text-mute mt-1.5 uppercase tracking-wider">
                    最近 {m.latest_date}
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {/* ── Tier timeline ── */}
      {d.recent_30d && d.recent_30d.some((r) => r.tier) && (
        <section className="py-10 border-b border-ink">
          <div className="kicker mb-4">— 30 日 TIER 演变 —</div>
          <h2 className="font-serif font-black text-[48px] leading-[1.05] tracking-[-0.02em] mb-6">
            分档<em className="not-italic text-gold-dim italic font-bold">变迁</em>
          </h2>
          <div className="flex gap-[2px]">
            {d.recent_30d.map((r) => {
              const tier = r.tier
              if (!tier) return (
                <div
                  key={r.date}
                  className="flex-1 h-10 bg-paper-2 border border-ink/10"
                  title={`${r.date}`}
                />
              )
              return (
                <div
                  key={r.date}
                  className="flex-1 h-10 cursor-default transition-opacity hover:opacity-80"
                  style={{ background: TIER_COLOR[tier] || 'var(--mute)' }}
                  title={`${r.date}: ${tier}`}
                />
              )
            })}
          </div>
          <div className="flex justify-between mt-2 font-mono text-[10px] text-mute uppercase tracking-wider">
            <span>{d.recent_30d[0]?.date}</span>
            <span>{d.recent_30d[d.recent_30d.length - 1]?.date}</span>
          </div>
          {/* Legend */}
          <div className="flex flex-wrap gap-x-5 gap-y-1 mt-4 font-mono text-[11px] text-mute">
            {(['🔥 夯死了', '👑 顶级', '💪 人上人', '😐 NPC', '💩 拉完了', '☠️ 答辩'] as const).map((t) => (
              <span key={t} className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-3" style={{ background: TIER_COLOR[t] }} />
                {t}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* ── 基础条: theme/sector + medals summary ── */}
      <section className="py-10">
        <div className="kicker mb-4">— 基础档案 —</div>
        <div className="flex flex-wrap gap-6 items-baseline">
          {d.theme && (
            <div>
              <span className="font-mono text-[11px] text-mute uppercase tracking-wider">板块</span>
              <span className="ml-2 font-mono font-medium text-ink">{d.theme}</span>
            </div>
          )}
          {d.persona && (
            <div>
              <span className="font-mono text-[11px] text-mute uppercase tracking-wider">人物</span>
              <span className="ml-2"><PersonaPill persona={d.persona} /></span>
            </div>
          )}
          <div>
            <span className="font-mono text-[11px] text-mute uppercase tracking-wider">累计奖牌</span>
            <span className="ml-2 font-mono font-bold text-gold text-[18px] tabular-nums">
              {Object.values(d.medal_count).reduce((a, b) => a + b, 0)}
            </span>
          </div>
          {d.medal_history.length > 0 && (
            <div>
              <span className="font-mono text-[11px] text-mute uppercase tracking-wider">最佳奖</span>
              <span className="ml-2 font-serif font-bold text-ink">{d.medal_history[0].name}</span>
            </div>
          )}
        </div>
        {/* Current tier */}
        {d.recent_30d && d.recent_30d.length > 0 && d.recent_30d[d.recent_30d.length - 1].tier && (
          <div className="mt-5 flex items-center gap-3">
            <span className="font-mono text-[11px] text-mute uppercase tracking-wider">当日 tier</span>
            <TierBadge tier={d.recent_30d[d.recent_30d.length - 1].tier!} />
          </div>
        )}
      </section>
    </>
  )
}