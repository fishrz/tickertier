import { useQuery } from '@tanstack/react-query'
import { getAwardsToday } from '@/lib/api'
import { AwardCard } from '@/components/AwardCard'
import { TierDistributionBar } from '@/components/TierDistributionBar'
import { formatPercent } from '@/lib/format'
import type { AwardGroup } from '@/types'

function findAward(awards: AwardGroup[], code: string): AwardGroup | undefined {
  return awards.find((a) => a.code === code)
}

function StatTile({ label, ticker, value }: { label: string; ticker?: string; value?: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface px-4 py-3 min-w-0">
      <div className="text-xs text-muted zh truncate">{label}</div>
      <div className="flex items-baseline gap-2 mt-1 min-w-0">
        <span className="font-mono text-sm text-text truncate">{ticker ?? '—'}</span>
        <span className="tabular text-gold font-semibold text-lg">{value ?? '—'}</span>
      </div>
    </div>
  )
}

export default function Today() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['awards-today'],
    queryFn: getAwardsToday,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-32 rounded-2xl bg-surface animate-pulse" />
        <div className="h-12 rounded-2xl bg-surface animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-48 rounded-2xl bg-surface animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return <div className="text-muted zh py-20 text-center">今日颁奖数据暂未生成</div>
  }

  const champion = findAward(data.awards, 'champion')
  const clown = findAward(data.awards, 'daily_clown')
  const rocket = findAward(data.awards, 'rocket') ?? champion
  const crash = findAward(data.awards, 'crash') ?? clown

  return (
    <div className="space-y-8">
      {/* HERO */}
      <section className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">
        <div className="lg:col-span-3">
          <h1 className="zh">🎖️ 今日颁奖典礼</h1>
          <div className="text-muted text-sm mt-2 tabular">截至 {data.date}</div>
        </div>
        <div className="lg:col-span-2 grid grid-cols-2 gap-3">
          <StatTile
            label="今日股王"
            ticker={champion?.winners[0]?.ticker}
            value={champion?.winners[0] ? formatPercent(champion.winners[0].metric) : undefined}
          />
          <StatTile
            label="今日答辩"
            ticker={clown?.winners[0]?.ticker}
            value={clown?.winners[0] ? formatPercent(clown.winners[0].metric) : undefined}
          />
          <StatTile
            label="最大涨幅"
            ticker={rocket?.winners[0]?.ticker}
            value={rocket?.winners[0] ? formatPercent(rocket.winners[0].metric) : undefined}
          />
          <StatTile
            label="最大跌幅"
            ticker={crash?.winners[0]?.ticker}
            value={crash?.winners[0] ? formatPercent(crash.winners[0].metric) : undefined}
          />
        </div>
      </section>

      {/* TIER BAR */}
      <TierDistributionBar distribution={data.tier_distribution} />

      {/* WATERFALL */}
      <section className="columns-1 sm:columns-2 lg:columns-3 gap-6">
        {data.awards.map((a, i) => (
          <AwardCard key={a.code} award={a} index={i} />
        ))}
      </section>
    </div>
  )
}
