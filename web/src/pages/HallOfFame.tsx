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

type Period = 'D' | 'W' | 'M' | 'Q' | 'Y' | 'ALL'

const PERIODS: { key: Period; label: string }[] = [
  { key: 'D', label: 'D' },
  { key: 'W', label: 'W' },
  { key: 'M', label: 'M' },
  { key: 'Q', label: 'Q' },
  { key: 'Y', label: 'Y' },
  { key: 'ALL', label: 'ALL' },
]

export default function HallOfFame() {
  const [period, setPeriod] = useState<Period>('ALL')

  const lbQ = useQuery({
    queryKey: ['leaderboard', period],
    queryFn: () => getLeaderboard(period, 20),
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
            周期 <b className="text-ink font-mono font-medium">{period === 'ALL' ? '全部' : period}</b>
          </span>
        }
      />

      {/* Period switcher */}
      <div className="flex gap-0 border-t border-ink -mt-6 mb-10">
        {PERIODS.map((p) => (
          <button
            key={p.key}
            onClick={() => setPeriod(p.key)}
            className={`font-mono text-[13px] tracking-[0.15em] uppercase px-5 py-3 border-b-[3px] transition-colors ${
              period === p.key
                ? 'bg-ink text-gold border-gold'
                : 'bg-paper text-mute border-transparent hover:text-ink'
            }`}
          >
            {p.label}
          </button>
        ))}
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
              <th className="font-mono text-[11px] uppercase tracking-[0.15em] py-2 pr-3 text-mute">Persona</th>
              <th className="font-mono text-[11px] uppercase tracking-[0.15em] py-2 text-right text-mute">①</th>
              <th className="font-mono text-[11px] uppercase tracking-[0.15em] py-2 text-right text-mute">②</th>
              <th className="font-mono text-[11px] uppercase tracking-[0.15em] py-2 text-right text-mute">③</th>
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
        <span className="text-mute"> ({topGold.gold}①)</span>
      </div>
      <div>
        <span className="text-mute">奖牌王</span>{' '}
        <Link to={`/stock/${mostMedals.ticker}`} className="font-bold text-ink hover:text-gold-dim">
          {mostMedals.ticker}
        </Link>
        <span className="text-mute"> ({mostMedals.total}枚)</span>
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