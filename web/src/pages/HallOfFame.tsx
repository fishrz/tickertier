import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getLeaderboard, getAwardTopByCode } from '@/lib/api'
import { Hero } from '@/components/Hero'
import { StockChip } from '@/components/StockChip'
import { PersonaPill } from '@/components/PersonaPill'
import { MEDALS } from '@/lib/format'
import { AWARD_META } from '@/lib/awards'
import { AwardInfoButton } from '@/components/AwardInfoButton'

type Window = '7d' | '30d' | '90d' | '180d' | '1y' | '3y' | 'all'
type Granularity = 'ALL' | 'D' | 'W' | 'M' | 'Q' | 'H' | 'Y' | 'E'

const WINDOWS: { key: Window; label: string }[] = [
  { key: '7d',  label: '近 7 日' },
  { key: '30d', label: '近 30 日' },
  { key: '90d', label: '近 90 日' },
  { key: '1y',  label: '近 1 年' },
  { key: '3y',  label: '近 3 年' },
  { key: 'all', label: '全部' },
]

const GRANULARITIES: { key: Granularity; label: string; hint: string }[] = [
  { key: 'ALL', label: '全部',   hint: '所有奖项一起算' },
  { key: 'D',   label: '每日',   hint: '日度评选：股王/答辩/过山车/影帝...' },
  { key: 'W',   label: '每周',   hint: '周度评选：暴兵/抗揍/反指' },
  { key: 'M',   label: '每月',   hint: '月度评选' },
  { key: 'Q',   label: '每季',   hint: '季度评选' },
  { key: 'Y',   label: '每年',   hint: '年度评选：劳模/万年老二/细水长流' },
  { key: 'E',   label: '财报',   hint: '财报披露窗口：封神/现形' },
]

export default function HallOfFame() {
  const [win, setWin] = useState<Window>('1y')
  const [gran, setGran] = useState<Granularity>('ALL')

  const lbQ = useQuery({
    queryKey: ['leaderboard', win, gran],
    queryFn: () => getLeaderboard({ window: win, granularity: gran, limit: 20 }),
  })

  if (lbQ.isLoading) {
    return <div className="py-32 text-center kicker">— 载入中 —</div>
  }
  if (lbQ.isError || !lbQ.data) {
    return (
      <div className="py-32 text-center text-neg font-mono text-sm">
        加载失败: {(lbQ.error as Error)?.message || '未知错误'}
      </div>
    )
  }

  const rows = lbQ.data
  const winLabel = WINDOWS.find((w) => w.key === win)?.label ?? win
  const granLabel = GRANULARITIES.find((g) => g.key === gran)?.label ?? gran

  return (
    <>
      <Hero
        title={
          <>
            <span className="block">名人堂</span>
            <span className="block text-[0.35em] text-mute font-mono tracking-[0.15em] uppercase">
              Hall of Fame
            </span>
          </>
        }
        bigStat={rows.length}
        bigStatLabel="支股票上榜"
        bottomLine={
          <span>
            <b className="text-ink font-mono font-medium">{winLabel}</b>
            <span className="text-mute"> · </span>
            <b className="text-ink font-mono font-medium">{granLabel}</b>
          </span>
        }
      />

      {/* Dual-axis selector — sits BELOW Hero, no negative margin (avoids border collision) */}
      <div className="mb-10 mt-4">
        {/* Axis 1: time window — primary */}
        <div className="flex items-baseline gap-4 px-1 pt-3 pb-2 border-b border-ink/15">
          <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-mute shrink-0 w-20">时间窗</span>
          <div className="flex flex-wrap">
            {WINDOWS.map((w) => (
              <button
                key={w.key}
                onClick={() => setWin(w.key)}
                className={`font-mono text-[12px] tracking-[0.05em] px-3 py-1.5 border-b-[2px] transition-colors ${
                  win === w.key
                    ? 'text-ink border-gold font-bold'
                    : 'text-mute border-transparent hover:text-ink'
                }`}
              >
                {w.label}
              </button>
            ))}
          </div>
        </div>
        {/* Axis 2: award granularity — secondary */}
        <div className="flex items-baseline gap-4 px-1 pt-2 pb-2">
          <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-mute shrink-0 w-20">奖项类型</span>
          <div className="flex flex-wrap">
            {GRANULARITIES.map((g) => (
              <button
                key={g.key}
                onClick={() => setGran(g.key)}
                title={g.hint}
                className={`font-mono text-[12px] tracking-[0.05em] px-3 py-1.5 border-b-[2px] transition-colors ${
                  gran === g.key
                    ? 'text-ink border-ink font-bold'
                    : 'text-mute border-transparent hover:text-ink'
                }`}
              >
                {g.label}
              </button>
            ))}
          </div>
        </div>
        {/* tiny inline help — only when something other than ALL is selected */}
        {gran !== 'ALL' && (
          <div className="mt-1 px-1 font-mono text-[11px] text-mute italic">
            ↑ {GRANULARITIES.find(g => g.key === gran)?.hint}
          </div>
        )}
      </div>

      {/* Top 20 leaderboard table */}
      <section className="mb-16">
        <div className="kicker mb-3">— 累计奖牌榜 —</div>
        <h2 className="font-serif font-black text-[40px] leading-none tracking-[-0.02em] mb-6">
          金<em className="not-italic text-gold-dim font-bold">·</em>银<em className="not-italic text-gold-dim font-bold">·</em>铜
        </h2>

        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b-[3px] border-ink text-left">
              <th className="font-mono text-[11px] uppercase tracking-[0.15em] py-2 pr-3 text-mute">#</th>
              <th className="font-mono text-[11px] uppercase tracking-[0.15em] py-2 pr-3 text-mute">Ticker</th>
              <th className="font-mono text-[11px] uppercase tracking-[0.15em] py-2 pr-3 text-mute">人物</th>
              <th className="font-serif text-[13px] py-2 text-right font-bold text-gold">金</th>
              <th className="font-serif text-[13px] py-2 text-right font-bold text-gold-dim">银</th>
              <th className="font-serif text-[13px] py-2 text-right font-bold text-ink/60">铜</th>
              <th className="font-mono text-[11px] uppercase tracking-[0.15em] py-2 pl-6 text-right text-mute">总计</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={row.ticker}
                className="border-b border-ink/15 group hover:bg-paper-2 transition-colors"
              >
                <td className="py-2.5 pr-3 font-serif font-black text-[18px] text-mute">{i + 1}</td>
                <td className="py-2.5 pr-3">
                  <StockChip ticker={row.ticker} />
                </td>
                <td className="py-2.5 pr-3">
                  <PersonaPill persona={row.persona} />
                </td>
                <td className="py-2.5 text-right font-mono font-bold text-[16px] text-gold tabular-nums">{row.gold}</td>
                <td className="py-2.5 text-right font-mono font-medium text-[15px] text-ink tabular-nums">{row.silver}</td>
                <td className="py-2.5 text-right font-mono text-[14px] text-ink/60 tabular-nums">{row.bronze}</td>
                <td className="py-2.5 pl-6 text-right font-mono font-bold text-[16px] tabular-nums border-l-[3px] border-ink">{row.total}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Award-by-award top 3 */}
      <section className="mb-16">
        <div className="kicker mb-3">— 单奖项排行 —</div>
        <h2 className="font-serif font-black text-[40px] leading-none tracking-[-0.02em] mb-8">
          各项<em className="not-italic text-gold-dim font-bold">之王</em>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 border-t border-ink">
          {AWARD_CODES.map((code) => (
            <AwardCard key={code} code={code} />
          ))}
        </div>
      </section>

      {/* Trivia bar */}
      <section className="border-t-[4px] border-ink py-8">
        <TriviaBar rows={rows} />
      </section>
    </>
  )
}

/* ─── Award code list (all 17) + meta ─── */

const AWARD_CODES = Object.keys(AWARD_META)

/* ─── Single award card with top 3 ─── */

function AwardCard({ code }: { code: string }) {
  const meta = AWARD_META[code as keyof typeof AWARD_META]
  const topQ = useQuery({
    queryKey: ['award-top', code],
    queryFn: () => getAwardTopByCode(code, 3),
    staleTime: 5 * 60 * 1000,
  })

  return (
    <article className="px-6 pt-6 pb-5 border-b border-r border-ink last:border-r-0">
      <header className="mb-4">
        <div className="font-serif font-black text-[22px] tracking-[-0.01em] leading-tight mb-1 flex items-start gap-2">
          <span className="flex-1 min-w-0">{meta?.name ?? code}</span>
          <span className="pt-[7px] shrink-0">
            <AwardInfoButton code={code} shortDesc={meta?.desc} />
          </span>
        </div>
        <div className="text-[12px] text-mute tracking-wider">{meta?.desc ?? ''}</div>
      </header>
      {topQ.isLoading ? (
        <div className="text-mute font-mono text-[12px] py-4">…</div>
      ) : topQ.data ? (
        <div className="flex flex-col gap-1.5">
          {topQ.data.map((entry, i) => (
            <div key={entry.ticker} className="flex items-baseline gap-2">
              <span className={`font-serif font-bold leading-none ${i === 0 ? 'text-[18px] text-gold' : 'text-[15px] text-gold-dim'}`}>
                {MEDALS[i]}
              </span>
              <Link to={`/stock/${entry.ticker}`} className="font-mono font-bold text-[14px] hover:text-gold-dim">
                {entry.ticker}
              </Link>
              <span className="text-mute font-mono text-[12px] ml-auto tabular-nums">
                {entry.gold}金 {entry.silver}银 {entry.bronze}铜
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-mute font-mono text-[12px] py-4">—</div>
      )}
    </article>
  )
}

/* ─── Trivia bar ─── */

function TriviaBar({ rows }: { rows: { ticker: string; gold: number; silver: number; bronze: number; total: number; persona: string | null }[] }) {
  if (!rows || rows.length === 0) return null

  const topGold = rows.reduce((best, r) => r.gold > best.gold ? r : best, rows[0])
  const mostMedals = rows.reduce((best, r) => r.total > best.total ? r : best, rows[0])

  return (
    <div className="flex flex-wrap gap-8 font-mono text-[13px] tracking-[0.04em]">
      <div>
        <span className="text-mute">金币王</span>{' '}
        <Link to={`/stock/${topGold.ticker}`} className="font-bold text-gold hover:text-gold-dim">
          {topGold.ticker}
        </Link>
        <span className="text-mute"> ({topGold.gold} 金)</span>
      </div>
      <div>
        <span className="text-mute">奖牌王</span>{' '}
        <Link to={`/stock/${mostMedals.ticker}`} className="font-bold text-ink hover:text-gold-dim">
          {mostMedals.ticker}
        </Link>
        <span className="text-mute"> ({mostMedals.total} 枚)</span>
      </div>
      {mostMedals.persona && (
        <div>
          <span className="text-mute">人物</span>{' '}
          <span className="text-gold-dim">{mostMedals.persona}</span>
        </div>
      )}
    </div>
  )
}