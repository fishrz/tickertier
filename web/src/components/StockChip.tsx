import { Link } from 'react-router-dom'

interface Props {
  ticker: string
  className?: string
}

// Mono ticker chip — inline element, hairline border, no rounded corners.
export function StockChip({ ticker, className = '' }: Props) {
  return (
    <Link
      to={`/stock/${ticker}`}
      className={`inline-block font-mono font-medium text-[13px] px-2.5 py-1 border border-ink bg-paper text-ink hover:bg-ink hover:text-paper transition-colors ${className}`}
    >
      {ticker}
    </Link>
  )
}
