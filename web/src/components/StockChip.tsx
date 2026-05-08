import { Link } from 'react-router-dom'
import { PersonaPill } from './PersonaPill'

export interface StockChipProps {
  ticker: string
  persona?: string | null
  clickable?: boolean
}

export function StockChip({ ticker, persona, clickable = true }: StockChipProps) {
  const inner = (
    <span className="font-mono text-[14px] text-text hover:text-gold transition-colors">
      {ticker}
    </span>
  )
  return (
    <span className="inline-flex flex-col items-start gap-1">
      {clickable ? <Link to={`/stock/${ticker}`}>{inner}</Link> : inner}
      {persona ? <PersonaPill persona={persona} /> : null}
    </span>
  )
}
