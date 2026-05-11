import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { getAwardsToday, getTodayTiers } from '@/lib/api'
import { TierBar } from '@/components/TierBar'

const TIER_ORDER = ['🔥 夯死了', '👑 顶级', '💪 人上人', '😐 NPC', '💩 拉完了', '☠️ 答辩']

function formatPct(v: number): string {
  const pct = Math.abs(v) <= 1 ? v * 100 : v
  const sign = pct > 0 ? '+' : ''
  return `${sign}${pct.toFixed(2)}%`
}

// Award codes where metric is a percent (return rate)
const PCT_AWARDS = new Set([
  'daily_king', 'daily_clown', 'champion', 'crap', 'tank', 'rocket', 'comeback',
  'high_dive', 'roller_coaster', 'volatile', 'gap', 'buy_low', 'big_position',
])

function formatMetric(code: string, v: number): string {
  if (PCT_AWARDS.has(code)) return formatPct(v)
  // Generic numeric: dollars / counts — show with thousand separator
  const abs = Math.abs(v)
  if (abs >= 1000) return v.toLocaleString('en-US', { maximumFractionDigits: 0 })
  if (abs >= 10) return v.toFixed(2)
  return v.toFixed(3)
}

function findAward(awards: Array<{ code: string; name: string; winners: Array<{ rank: number; ticker: string; metric: number }> }>, code: string) {
  return awards.find((a) => a.code === code) || null
}

function topWinner(award: ReturnType<typeof findAward>) {
  if (!award || !award.winners?.length) return null
  return award.winners.find((w) => w.rank === 1) || award.winners[0]
}

export default function Daily() {
  const awardsQ = useQuery({ queryKey: ['awards', 'today'], queryFn: getAwardsToday })
  const tiersQ = useQuery({ queryKey: ['tiers', 'today'], queryFn: getTodayTiers })
  const [shareToast, setShareToast] = useState<string | null>(null)

  if (awardsQ.isLoading) return <div className="py-32 text-center kicker">— LOADING —</div>
  if (awardsQ.isError || !awardsQ.data) {
    return (
      <div className="py-32 text-center text-neg font-mono text-sm">
        加载失败: {(awardsQ.error as Error)?.message || '未知错误'}
      </div>
    )
  }

  const data = awardsQ.data
  const king = topWinner(findAward(data.awards, 'daily_king'))
  const clown = topWinner(findAward(data.awards, 'daily_clown'))
  const totalUniverse = Object.values(data.tier_distribution).reduce((a, b) => a + b, 0)

  // Sort awards keeping daily_king + daily_clown first
  const FEATURED = new Set(['daily_king', 'daily_clown'])
  const featured = data.awards.filter((a) => FEATURED.has(a.code))
  const rest = data.awards.filter((a) => !FEATURED.has(a.code))

  const handleShare = async () => {
    const kingStr = king ? `🏆 ${king.ticker} ${formatPct(king.metric)}` : ''
    const clownStr = clown ? `💩 ${clown.ticker} ${formatPct(clown.metric)}` : ''
    const text = `📅 ${data.date} · 夯股日报\n${kingStr}\n${clownStr}\n🌐 ${window.location.origin}/daily`
    try {
      if (navigator.share) {
        await navigator.share({ title: '夯股日报', text, url: `${window.location.origin}/daily` })
        return
      }
    } catch (e) {
      // fall through to clipboard
    }
    try {
      await navigator.clipboard.writeText(text)
      setShareToast('已复制到剪贴板')
      setTimeout(() => setShareToast(null), 2000)
    } catch (e) {
      setShareToast('分享失败')
      setTimeout(() => setShareToast(null), 2000)
    }
  }

  return (
    <>
      {/* ── Date banner ── */}
      <section className="pt-8 pb-4 border-b border-ink">
        <div className="kicker mb-2">— 今日颁奖典礼 · DAILY AWARDS —</div>
        <div className="flex items-baseline justify-between flex-wrap gap-3">
          <h1 className="font-serif font-black tracking-[-0.04em] leading-[0.92] text-[clamp(64px,8vw,108px)]">
            {data.date}
          </h1>
          <button
            onClick={handleShare}
            className="font-mono text-[11px] uppercase tracking-[0.2em] px-4 py-2 border border-ink hover:bg-ink hover:text-paper transition-colors"
          >
            分享今日 →
          </button>
        </div>
        {shareToast && (
          <div className="mt-3 font-mono text-[11px] text-gold-dim">{shareToast}</div>
        )}
      </section>

      {/* ── King + Clown duo hero ── */}
      <section className="grid grid-cols-1 md:grid-cols-2 border-b border-ink">
        {king && (
          <Link
            to={`/stock/${king.ticker}`}
            className="block py-12 px-2 md:pr-8 md:border-r border-ink hover:bg-ink/[0.03] transition-colors"
          >
            <div className="kicker mb-3 text-gold-dim">— 🏆 今日股王 —</div>
            <div className="font-serif font-black text-[clamp(72px,11vw,140px)] leading-[0.88] tracking-[-0.04em]">
              {king.ticker}
            </div>
            <div className="font-mono font-bold text-pos text-[clamp(28px,4vw,44px)] tabular-nums mt-3">
              {formatPct(king.metric)}
            </div>
            <div className="font-mono text-[11px] text-mute uppercase tracking-[0.15em] mt-3">
              今日最强 →
            </div>
          </Link>
        )}
        {clown && (
          <Link
            to={`/stock/${clown.ticker}`}
            className="block py-12 px-2 md:pl-8 hover:bg-ink/[0.03] transition-colors"
          >
            <div className="kicker mb-3 text-neg">— 💩 今日答辩 —</div>
            <div className="font-serif font-black text-[clamp(72px,11vw,140px)] leading-[0.88] tracking-[-0.04em]">
              {clown.ticker}
            </div>
            <div className="font-mono font-bold text-neg text-[clamp(28px,4vw,44px)] tabular-nums mt-3">
              {formatPct(clown.metric)}
            </div>
            <div className="font-mono text-[11px] text-mute uppercase tracking-[0.15em] mt-3">
              今日最菜 →
            </div>
          </Link>
        )}
      </section>

      {/* ── Tier distribution ── */}
      <TierBar distribution={data.tier_distribution} />

      {/* ── Stats line ── */}
      <section className="py-6 border-b border-ink flex items-baseline gap-6 flex-wrap font-mono text-[12px] uppercase tracking-[0.1em] text-mute">
        <span>UNIVERSE <b className="text-ink font-bold">{totalUniverse}</b> 支</span>
        <span>AWARDS <b className="text-ink font-bold">{data.awards.length}</b> 项</span>
        <span>FEATURED <b className="text-ink font-bold">{featured.length}</b></span>
      </section>

      {/* ── All awards compact list ── */}
      <section className="py-10">
        <div className="kicker mb-6">— 今日全部奖项 —</div>
        <ul className="divide-y divide-ink/15 border-y border-ink">
          {rest.map((a) => {
            const top = topWinner(a)
            if (!top) return null
            return (
              <li key={a.code}>
                <Link
                  to={`/stock/${top.ticker}`}
                  className="flex items-baseline gap-4 py-3 px-1 hover:bg-ink/[0.04] transition-colors"
                >
                  <span className="font-mono text-[12px] text-mute w-[44px] tabular-nums">#{top.rank}</span>
                  <span className="font-serif font-bold text-[16px] flex-1 truncate">{a.name}</span>
                  <span className="font-mono font-bold text-[15px] tabular-nums">{top.ticker}</span>
                  <span className="font-mono text-[12px] text-mute tabular-nums w-[80px] text-right">
                    {top.metric != null ? formatMetric(a.code, top.metric) : ''}
                  </span>
                </Link>
              </li>
            )
          })}
        </ul>
      </section>

      {/* ── Tier teaser ── */}
      {tiersQ.data && (
        <section className="py-10 border-t border-ink">
          <div className="kicker mb-6">— 分档速览 —</div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-4">
            {TIER_ORDER.map((tier) => {
              const members = tiersQ.data?.members?.[tier] || []
              if (!members.length) return null
              return (
                <div key={tier}>
                  <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-mute mb-1">
                    {tier} · {members.length}
                  </div>
                  <div className="text-[13px] leading-relaxed">
                    {members.slice(0, 5).map((t, i) => (
                      <span key={t}>
                        <Link to={`/stock/${t}`} className="font-mono hover:text-gold-dim">{t}</Link>
                        {i < Math.min(4, members.length - 1) ? <span className="text-mute">, </span> : null}
                      </span>
                    ))}
                    {members.length > 5 && <span className="text-mute"> +{members.length - 5}</span>}
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* ── Bottom CTAs ── */}
      <section className="py-8 border-t border-ink flex flex-wrap gap-3 font-mono text-[11px] uppercase tracking-[0.15em]">
        <Link to="/" className="px-4 py-2 border border-ink hover:bg-ink hover:text-paper transition-colors">完整颁奖 →</Link>
        <Link to="/hall" className="px-4 py-2 border border-ink hover:bg-ink hover:text-paper transition-colors">名人堂 →</Link>
        <Link to="/race" className="px-4 py-2 border border-ink hover:bg-ink hover:text-paper transition-colors">排名变迁 →</Link>
      </section>
    </>
  )
}
