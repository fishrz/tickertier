import { useQuery } from '@tanstack/react-query'
import { getAwardsToday, getTodayTiers } from '@/lib/api'
import { Hero } from '@/components/Hero'
import { TierBar } from '@/components/TierBar'
import { AwardCard } from '@/components/AwardCard'
import { TierTable } from '@/components/TierTable'

// Narrative ordering — major awards first, then drama, then rhythm
const ORDER_HINT = [
  'champion', 'stock_king',          // 主奖
  'crap', 'tank', 'daily_clown',     // 反派
  'comeback', 'rocket',              // 戏剧
  'high_dive', 'roller_coaster', 'volatile', 'oscar',
  'gap', 'gambler',
  'workhorse', 'silver_curse',
  'steady_grind', 'antifragile',
  'reverse_idx', 'npc_god',
  'pillar', 'traitor',
  'earnings_god',
]
function awardRank(code: string): number {
  for (let i = 0; i < ORDER_HINT.length; i++) {
    if (code.includes(ORDER_HINT[i])) return i
  }
  return 999
}

export default function Today() {
  const awardsQ = useQuery({ queryKey: ['awards', 'today'], queryFn: getAwardsToday })
  const tiersQ = useQuery({ queryKey: ['tiers', 'today'], queryFn: getTodayTiers })

  if (awardsQ.isLoading) {
    return (
      <div className="py-32 text-center kicker">— LOADING —</div>
    )
  }
  if (awardsQ.isError || !awardsQ.data) {
    return (
      <div className="py-32 text-center text-neg font-mono text-sm">
        加载失败: {(awardsQ.error as Error)?.message || '未知错误'}
      </div>
    )
  }

  const data = awardsQ.data
  const sorted = [...data.awards].sort((a, b) => awardRank(a.code) - awardRank(b.code))
  const totalTiers = Object.values(data.tier_distribution).reduce((a, b) => a + b, 0)

  return (
    <>
      <Hero
        title={
          <>
            <span className="block">今日</span>
            <span className="block"><em className="not-italic font-bold text-gold-dim italic">颁奖</em>之夜</span>
          </>
        }
        bigStat={data.awards.length}
        bigStatLabel="项今日奖颁出"
        bottomLine={
          <>
            UNIVERSE <b className="text-ink font-mono font-medium">{totalTiers}</b> 支
          </>
        }
      />

      <TierBar distribution={data.tier_distribution} />

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 border-b border-ink">
        {sorted.map((a) => (
          <AwardCard key={a.code} award={a} />
        ))}
      </section>

      <section className="pt-14">
        <div className="kicker mb-2">— 完整 TIER 榜 —</div>
        <h2 className="font-serif font-black text-[56px] leading-none tracking-[-0.03em] mb-2">
          夯<em className="not-italic text-gold-dim italic font-bold">/</em>顶
          <em className="not-italic text-gold-dim italic font-bold">/</em>NPC
          <em className="not-italic text-gold-dim italic font-bold">/</em>拉
        </h2>
        <p className="text-sm text-mute mb-8 max-w-[600px] leading-relaxed">
          81 支 AI 基建标的按今日综合表现（涨跌相对 QQQ 修正 + 振幅 + 量能）分档。点 ticker 看履历。
        </p>
        {tiersQ.data ? (
          <TierTable members={tiersQ.data.members} />
        ) : (
          <div className="py-12 text-center kicker">— LOADING TIERS —</div>
        )}
      </section>
    </>
  )
}
