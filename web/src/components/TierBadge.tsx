import { motion } from 'framer-motion'
import type { TierName } from '@/types'
import { cn } from '@/lib/format'

const TIER_STYLES: Record<TierName, { bg: string; text: string; border?: string }> = {
  '🔥 夯死了': { bg: 'bg-tier-fire', text: 'text-white' },
  '👑 顶级': { bg: 'bg-tier-crown', text: 'text-black' },
  '💪 人上人': { bg: 'bg-tier-jade', text: 'text-black' },
  '😐 NPC': { bg: 'bg-tier-npc', text: 'text-white' },
  '💩 拉完了': { bg: 'bg-tier-poop', text: 'text-white' },
  '☠️ 答辩': { bg: 'bg-tier-skull', text: 'text-[#9A95A8]', border: 'border border-tier-fire' },
}

const SIZE_STYLES = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-3 py-1',
  lg: 'text-base px-4 py-1.5',
}

export interface TierBadgeProps {
  tier: TierName
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function TierBadge({ tier, size = 'md', className }: TierBadgeProps) {
  const style = TIER_STYLES[tier]
  const base = cn(
    'inline-flex items-center gap-1 rounded-full font-medium whitespace-nowrap zh',
    SIZE_STYLES[size],
    style.bg,
    style.text,
    style.border,
    className,
  )

  if (tier === '🔥 夯死了') {
    return (
      <motion.span
        className={base}
        animate={{ boxShadow: ['0 0 0 0 rgba(255,61,113,0.5)', '0 0 0 8px rgba(255,61,113,0)'] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        {tier}
      </motion.span>
    )
  }
  return <span className={base}>{tier}</span>
}
