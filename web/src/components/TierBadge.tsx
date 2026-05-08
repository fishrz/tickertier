import type { TierName } from '@/types'

// Compact tier badge used inline (e.g. on stock detail / persona pill row)
const STRIPE: Record<TierName, string> = {
  '🔥 夯死了': 'var(--tier-fire)',
  '👑 顶级': 'var(--tier-crown)',
  '💪 人上人': 'var(--tier-jade)',
  '😐 NPC': 'var(--tier-npc)',
  '💩 拉完了': 'var(--tier-poop)',
  '☠️ 答辩': 'var(--tier-skull)',
}

interface Props {
  tier: TierName | string
  className?: string
}

export function TierBadge({ tier, className = '' }: Props) {
  const stripe = STRIPE[tier as TierName] || 'var(--ink)'
  const isFire = tier === '🔥 夯死了'
  const isSkull = tier === '☠️ 答辩'
  const containerCls = isFire
    ? 'bg-ink text-gold border-ink'
    : isSkull
    ? 'bg-neg text-paper border-neg'
    : 'bg-paper text-ink border-ink'
  return (
    <span
      className={`inline-flex items-center font-mono text-[11px] uppercase tracking-[0.15em] py-[3px] pl-2 pr-2.5 border ${containerCls} ${className}`}
      style={{ borderLeftWidth: 4, borderLeftColor: stripe }}
    >
      {tier}
    </span>
  )
}
