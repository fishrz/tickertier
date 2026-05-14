import { useQuery } from '@tanstack/react-query'
import { getAwardsToday, getTodayTiers } from '@/lib/api'
import { Hero } from '@/components/Hero'
import { TierBar } from '@/components/TierBar'
import { AwardCard } from '@/components/AwardCard'
import { TierTable } from '@/components/TierTable'

// Narrative ordering — major awards first, then drama, portfolio, rhythm
const ORDER_HINT = [
  'daily_king',       // 今日股王必须第一
  'daily_clown',      // 今日答辩第二
  'comeback', 'roller_coaster', 'oscar', 'pump_army', 'npc_god', 'tank',
  'pillar', 'traitor', 'cash_king', 'tear_jerker', 'big_position', 'buy_low',
  'earnings_god', 'earnings_clown',
  'workhorse', 'silver_curse', 'steady_grind', 'gambler', 'reverse_idx',
]
function awardRank(code: string): number {
  const exact = ORDER_HINT.indexOf(code)
  return exact >= 0 ? exact : 999
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
