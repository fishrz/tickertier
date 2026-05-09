import type { TierName } from '@/types'

// Tier color used only in stripe / chip border, never as background fill
const TIER_STRIPE: Record<TierName, string> = {
  '🔥 夯死了': 'var(--tier-fire)',
  '👑 顶级': 'var(--tier-crown)',
  '💪 人上人': 'var(--tier-jade)',
  '😐 NPC': 'var(--tier-npc)',
  '💩 拉完了': 'var(--tier-poop)',
  '☠️ 答辩': 'var(--tier-skull)',
}

const ORDER: TierName[] = [
  '🔥 夯死了', '👑 顶级', '💪 人上人', '😐 NPC', '💩 拉完了', '☠️ 答辩',
]

interface Props {
  distribution: Record<string, number>
  label?: string
}

export function TierBar({ distribution, label = '今日全场 TIER 分布' }: Props) {
  return (
    <section className="pt-7 pb-8 border-b border-ink">
      <div className="kicker mb-3.5">— {label} —</div>
      <div className="flex h-2 mb-3">
        {ORDER.map((t) => {
          const n = distribution[t] || 0
          if (!n) return null
          return (
            <div
              key={t}
              style={{ flex: n, background: TIER_STRIPE[t] }}
              title={`${t} ${n}支`}
            />
          )
        })}
      </div>
      <div className="flex flex-wrap gap-x-6 gap-y-2 font-mono text-[11px] text-mute">
        {ORDER.map((t) => (
          <span key={t}>
            {t} <b className="text-ink font-medium">{distribution[t] || 0}</b>
          </span>
        ))}
      </div>
    </section>
  )
}
