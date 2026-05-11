import { useEffect, useState } from 'react'
import {
  addToWatchlist,
  removeFromWatchlist,
  isInWatchlist,
  normalizeTicker,
} from '@/lib/watchlist'

/**
 * Star toggle button. Adds/removes the ticker from the user's local watchlist.
 * Does NOT touch portfolio data — watchlist is a separate, ticker-only layer.
 */
export function StarButton({
  ticker,
  size = 'md',
  className = '',
}: {
  ticker: string
  size?: 'sm' | 'md'
  className?: string
}) {
  const t = normalizeTicker(ticker)
  const [starred, setStarred] = useState<boolean>(false)

  // Sync from localStorage on mount + listen for cross-component changes
  useEffect(() => {
    if (!t) return
    setStarred(isInWatchlist(t))
    const onChange = () => setStarred(isInWatchlist(t))
    window.addEventListener('watchlist:change', onChange)
    window.addEventListener('storage', onChange)
    return () => {
      window.removeEventListener('watchlist:change', onChange)
      window.removeEventListener('storage', onChange)
    }
  }, [t])

  if (!t) return null

  const toggle = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (starred) {
      removeFromWatchlist(t)
      setStarred(false)
    } else {
      addToWatchlist(t)
      setStarred(true)
    }
  }

  const dim = size === 'sm' ? 'text-[14px] px-2 py-1' : 'text-[16px] px-3 py-1.5'
  const label = starred ? '★ 已关注' : '☆ 关注'

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={starred}
      title={starred ? '从关注列表移除' : '加入关注列表'}
      className={[
        'font-mono uppercase tracking-[0.15em] border border-ink',
        'transition-colors duration-150',
        starred
          ? 'bg-ink text-paper hover:bg-paper hover:text-ink'
          : 'bg-paper text-ink hover:bg-ink hover:text-paper',
        dim,
        className,
      ].join(' ')}
    >
      {label}
    </button>
  )
}
