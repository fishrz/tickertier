import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import type { AwardGroup } from '@/types'
import { MEDALS, formatMetric } from '@/lib/format'

export interface AwardCardProps {
  award: AwardGroup
  index?: number
}

export function AwardCard({ award, index = 0 }: AwardCardProps) {
  const emoji = [...award.name][0] ?? '🏆'
  const title = award.name.replace(emoji, '').trim() || award.name

  return (
    <motion.article
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35, ease: 'easeOut' }}
      className="break-inside-avoid mb-6 rounded-2xl border border-border bg-surface p-6 hover:border-gold-soft transition-colors"
    >
      <header className="flex items-start gap-3 mb-2">
        <span className="text-[32px] leading-none">{emoji}</span>
        <div className="flex-1 min-w-0">
          <h3 className="zh text-text">{title}</h3>
          <p className="text-muted italic text-sm zh mt-1">{award.description}</p>
        </div>
      </header>
      <div className="h-px bg-border my-4" />
      <ul className="space-y-2.5">
        {award.winners.length === 0 && (
          <li className="text-muted text-sm">…</li>
        )}
        {award.winners.slice(0, 3).map((w) => (
          <li key={`${w.rank}-${w.ticker}`} className="flex items-center gap-3">
            <span className="text-lg w-6 shrink-0">{MEDALS[w.rank - 1] ?? `${w.rank}.`}</span>
            <Link
              to={`/stock/${w.ticker}`}
              className="font-mono text-[16px] text-text hover:text-gold transition-colors w-20 shrink-0"
            >
              {w.ticker}
            </Link>
            <span className="tabular text-gold font-semibold flex-1">
              {formatMetric(award.code, w.metric)}
            </span>
          </li>
        ))}
      </ul>
    </motion.article>
  )
}
