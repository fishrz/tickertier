import { Link } from 'react-router-dom'
import type { AwardGroup } from '@/types'
import { formatMetric, MEDALS, metricTone } from '@/lib/format'

interface Props {
  award: AwardGroup
}

// Each award card = one "trading card": serif title, mono ranks ①②③
export function AwardCard({ award }: Props) {
  const winners = [...award.winners.slice(0, 3)]
  while (winners.length < 3) winners.push(null as any)

  return (
    <article className="px-6 pt-7 pb-6 border-r border-b border-ink last:border-r-0 [&:nth-child(3n)]:border-r-0">
      <header className="mb-5 min-h-[64px]">
        <div className="font-serif font-black text-[26px] tracking-[-0.01em] leading-[1.1] mb-1.5">
          {award.name}
        </div>
        <div className="text-[12px] text-mute tracking-wider">
          {award.description}
        </div>
      </header>
      <div className="flex flex-col">
        {winners.map((w, i) => {
          const isFirst = i === 0
          const headerCls = isFirst
            ? 'pt-3 border-t-[2px] border-ink'
            : 'pt-2 border-t border-paper-2'
          if (!w) {
            return (
              <div key={i} className={`grid grid-cols-[28px_1fr_auto] items-baseline gap-3 pb-2 opacity-30 ${headerCls}`}>
                <span className={`font-serif font-bold text-gold-dim leading-none ${isFirst ? 'text-[22px]' : 'text-[18px]'}`}>{MEDALS[i]}</span>
                <span className="font-mono font-bold">—</span>
                <span className="font-mono">—</span>
              </div>
            )
          }
          const tone = metricTone(award.code, w.metric)
          const toneCls = tone === 'pos' ? 'text-pos' : tone === 'neg' ? 'text-neg' : 'text-ink'
          return (
            <div key={i} className={`grid grid-cols-[28px_1fr_auto] items-baseline gap-3 pb-2 ${headerCls}`}>
              <span
                className={`font-serif font-bold leading-none ${isFirst ? 'text-[22px] text-gold' : 'text-[18px] text-gold-dim'}`}
              >
                {MEDALS[i]}
              </span>
              <Link
                to={`/stock/${w.ticker}`}
                className={`font-mono font-bold tracking-tight hover:text-gold-dim ${isFirst ? 'text-[22px]' : 'text-[18px]'}`}
              >
                {w.ticker}
              </Link>
              <span
                className={`font-mono tabular-nums ${toneCls} ${isFirst ? 'text-[16px] font-bold' : 'text-[14px] font-medium'}`}
              >
                {formatMetric(award.code, w.metric)}
              </span>
            </div>
          )
        })}
      </div>
    </article>
  )
}
