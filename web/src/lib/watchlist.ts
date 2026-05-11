// Watchlist: lightweight ticker-only list, separate from portfolio.
// Storage key is intentionally distinct from `tickertier_portfolio` so
// position data (cost basis, shares, weight, pnl) is NEVER touched here.
//
// URL-as-identity:
//   /watch                  -> read/write user's own watchlist
//   /watch?w=AAOI,ALAB,POET -> read-only "shared view" of someone else's list
//                              user can clone into their own with one click.

const STORAGE_KEY = 'tickertier_watchlist'
const MAX_SIZE = 200 // generous cap; sharing URLs stay under ~2KB
const TICKER_RE = /^[A-Z][A-Z0-9.\-]{0,9}$/

/** Normalize and validate a ticker (uppercase, alphanumeric + . -). */
export function normalizeTicker(raw: string): string | null {
  const t = raw.trim().toUpperCase()
  if (!t || !TICKER_RE.test(t)) return null
  return t
}

/** Sanitize an arbitrary list of tickers: dedup, normalize, cap length. */
export function sanitizeTickers(input: readonly string[]): string[] {
  const out: string[] = []
  const seen = new Set<string>()
  for (const raw of input) {
    const t = normalizeTicker(raw)
    if (!t || seen.has(t)) continue
    seen.add(t)
    out.push(t)
    if (out.length >= MAX_SIZE) break
  }
  return out
}

/** Load the user's local watchlist from localStorage. SSR-safe. */
export function loadWatchlist(): string[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return sanitizeTickers(parsed)
  } catch {
    return []
  }
}

/** Persist the watchlist to localStorage. Caller passes the full desired list. */
export function saveWatchlist(tickers: readonly string[]): string[] {
  const cleaned = sanitizeTickers(tickers)
  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cleaned))
    // Notify same-tab listeners (storage event only fires cross-tab).
    window.dispatchEvent(new CustomEvent('watchlist:change', { detail: cleaned }))
  }
  return cleaned
}

export function addToWatchlist(ticker: string): string[] {
  const t = normalizeTicker(ticker)
  if (!t) return loadWatchlist()
  const cur = loadWatchlist()
  if (cur.includes(t)) return cur
  return saveWatchlist([...cur, t])
}

export function removeFromWatchlist(ticker: string): string[] {
  const t = normalizeTicker(ticker)
  if (!t) return loadWatchlist()
  return saveWatchlist(loadWatchlist().filter((x) => x !== t))
}

export function isInWatchlist(ticker: string): boolean {
  const t = normalizeTicker(ticker)
  if (!t) return false
  return loadWatchlist().includes(t)
}

/** Parse the `?w=` URL param into a sanitized ticker list. */
export function parseWatchParam(search: string): string[] {
  try {
    const params = new URLSearchParams(search)
    const raw = params.get('w')
    if (!raw) return []
    return sanitizeTickers(raw.split(/[,;\s]+/))
  } catch {
    return []
  }
}

/** Build a shareable URL like `https://host/watch?w=AAOI,ALAB,POET`. */
export function buildShareUrl(tickers: readonly string[], origin?: string): string {
  const base =
    origin ??
    (typeof window !== 'undefined' ? window.location.origin : 'https://tickertier.vercel.app')
  const list = sanitizeTickers(tickers)
  if (list.length === 0) return `${base}/watch`
  return `${base}/watch?w=${list.join(',')}`
}
