import type { TierName } from '@/types'

const TIER_ORDER: TierName[] = [
  '🔥 夯死了',
  '👑 顶级',
  '💪 人上人',
  '😐 NPC',
  '💩 拉完了',
  '☠️ 答辩',
]

const TIER_BG: Record<TierName, string> = {
  '🔥 夯死了': 'bg-tier-fire',
  '👑 顶级': 'bg-tier-crown',
  '💪 人上人': 'bg-tier-jade',
  '😐 NPC': 'bg-tier-npc',
  '💩 拉完了': 'bg-tier-poop',
  '☠️ 答辩': 'bg-tier-skull',
}

export interface TierDistributionBarProps {
  distribution: Record<string, number>
}

export function TierDistributionBar({ distribution }: TierDistributionBarProps) {
  const entries = TIER_ORDER.map((t) => ({ tier: t, count: distribution[t] ?? 0 }))
  const total = entries.reduce((s, e) => s + e.count, 0)

  return (
    <section className="space-y-2">
      <div className="text-sm text-muted zh">
        今日 <span className="tabular text-text">{total}</span> 支股票 tier 分布
      </div>
      <div className="flex w-full h-6 rounded-lg overflow-hidden border border-border">
        {entries.map((e) => {
          if (e.count === 0) return null
          const pct = total > 0 ? (e.count / total) * 100 : 0
          return (
            <div
              key={e.tier}
              className={`${TIER_BG[e.tier]} flex items-center justify-center text-[11px] font-medium text-black/80`}
              style={{ width: `${pct}%` }}
              title={`${e.tier}: ${e.count}`}
            >
              {pct > 8 ? e.count : ''}
            </div>
          )
        })}
      </div>
      <div className="text-xs text-muted zh">
        {entries.map((e, i) => (
          <span key={e.tier}>
            {e.tier} <span className="tabular">{e.count}</span>
            {i < entries.length - 1 ? '，' : ''}
          </span>
        ))}
      </div>
    </section>
  )
}
