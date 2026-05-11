import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getStocks, type StockRow } from '@/lib/api'
import { formatPercent } from '@/lib/format'
import { TierBadge } from '@/components/TierBadge'
import {
  loadWatchlist,
  saveWatchlist,
  parseWatchParam,
  buildShareUrl,
  sanitizeTickers,
  removeFromWatchlist,
} from '@/lib/watchlist'

// Sort options
type SortKey = 'order' | 'pct_desc' | 'pct_asc' | 'awards_desc' | 'ticker'

function sortRows(rows: EnrichedRow[], key: SortKey): EnrichedRow[] {
  const out = [...rows]
  switch (key) {
    case 'pct_desc':
      out.sort((a, b) => (b.pct_change ?? -Infinity) - (a.pct_change ?? -Infinity))
      break
    case 'pct_asc':
      out.sort((a, b) => (a.pct_change ?? Infinity) - (b.pct_change ?? Infinity))
      break
    case 'awards_desc':
      out.sort((a, b) => (b.awards_count ?? 0) - (a.awards_count ?? 0))
      break
    case 'ticker':
      out.sort((a, b) => a.ticker.localeCompare(b.ticker))
      break
    case 'order':
    default:
      // preserve user order
      break
  }
  return out
}

interface EnrichedRow {
  ticker: string
  name: string | null
  close: number | null
  pct_change: number | null
  tier: string | null
  awards_count: number | null
  best_award: string | null
  found: boolean
}

function enrich(tickers: string[], stocks: StockRow[]): EnrichedRow[] {
  const map = new Map(stocks.map((s) => [s.ticker, s]))
  return tickers.map((t) => {
    const s = map.get(t)
    if (!s) {
      return {
        ticker: t,
        name: null,
        close: null,
        pct_change: null,
        tier: null,
        awards_count: null,
        best_award: null,
        found: false,
      }
    }
    return {
      ticker: t,
      name: s.name,
      close: s.close,
      pct_change: s.pct_change,
      tier: s.tier,
      awards_count: s.awards_count ?? 0,
      best_award: s.medal_history?.[0]?.name ?? null,
      found: true,
    }
  })
}

export default function Watchlist() {
  const [searchParams, setSearchParams] = useSearchParams()
  const sharedParam = useMemo(
    () => parseWatchParam(window.location.search),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [searchParams.toString()],
  )
  const isShared = sharedParam.length > 0

  // Local watchlist state (own list)
  const [tickers, setTickers] = useState<string[]>(() => loadWatchlist())
  useEffect(() => {
    const onChange = () => setTickers(loadWatchlist())
    window.addEventListener('watchlist:change', onChange)
    window.addEventListener('storage', onChange)
    return () => {
      window.removeEventListener('watchlist:change', onChange)
      window.removeEventListener('storage', onChange)
    }
  }, [])

  // Which list are we displaying?
  const displayTickers = isShared ? sharedParam : tickers

  const stocksQ = useQuery({
    queryKey: ['stocks'],
    queryFn: getStocks,
    staleTime: 5 * 60 * 1000,
  })

  const [sortKey, setSortKey] = useState<SortKey>('order')
  const [showShareCopied, setShowShareCopied] = useState(false)
  const [showAddInput, setShowAddInput] = useState(false)
  const [addText, setAddText] = useState('')

  const rows = useMemo(() => {
    if (!stocksQ.data) return []
    return sortRows(enrich(displayTickers, stocksQ.data), sortKey)
  }, [displayTickers, stocksQ.data, sortKey])

  const handleRemove = (ticker: string) => {
    removeFromWatchlist(ticker)
  }

  const handleAdd = () => {
    const parts = addText.split(/[,;\s]+/)
    const cleaned = sanitizeTickers([...tickers, ...parts])
    saveWatchlist(cleaned)
    setAddText('')
    setShowAddInput(false)
  }

  const handleCopyShare = async () => {
    const url = buildShareUrl(tickers)
    try {
      await navigator.clipboard.writeText(url)
      setShowShareCopied(true)
      setTimeout(() => setShowShareCopied(false), 1800)
    } catch {
      // fallback: prompt
      window.prompt('复制链接：', url)
    }
  }

  const handleCloneShared = () => {
    const merged = sanitizeTickers([...tickers, ...sharedParam])
    saveWatchlist(merged)
    // drop the ?w= param after cloning
    setSearchParams({}, { replace: true })
  }

  const handleClearShared = () => {
    setSearchParams({}, { replace: true })
  }

  // ── Render ──────────────────────────────────────────────
  const validPctRows = rows.filter((r) => r.pct_change != null)
  const avgPct =
    validPctRows.length > 0
      ? validPctRows.reduce((a, r) => a + (r.pct_change ?? 0), 0) / validPctRows.length
      : null

  return (
    <div className="max-w-page mx-auto px-[var(--page-pad-x)] py-10">
      {/* Header */}
      <section className="border-b border-ink pb-8 mb-8">
        <div className="kicker mb-3">— 关注列表 / WATCHLIST —</div>
        <div className="flex items-end justify-between gap-6 flex-wrap">
          <div>
            <h1 className="font-serif font-black tracking-[-0.03em] leading-[0.95] text-[clamp(48px,7vw,80px)]">
              {isShared ? '别人的关注' : '我的关注'}
            </h1>
            <p className="mt-3 text-mute font-mono text-[12px] uppercase tracking-[0.15em]">
              {isShared
                ? `共 ${sharedParam.length} 只 · 只读视图 · 可一键克隆到我的列表`
                : `共 ${tickers.length} 只 · 仅本地存储 · 不含持仓数据`}
            </p>
          </div>
          <div className="flex items-baseline gap-6 font-mono text-[12px]">
            {avgPct != null && (
              <div className="text-right">
                <div className="text-mute uppercase tracking-[0.15em] text-[10px]">今日均值</div>
                <div
                  className={`text-[24px] font-bold tabular-nums ${
                    avgPct > 0 ? 'text-pos' : avgPct < 0 ? 'text-neg' : 'text-ink'
                  }`}
                >
                  {formatPercent(avgPct)}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action bar */}
        <div className="mt-6 flex flex-wrap gap-3 items-center">
          {isShared ? (
            <>
              <button
                onClick={handleCloneShared}
                className="px-4 py-2 bg-ink text-paper font-mono text-[11px] uppercase tracking-[0.18em] hover:bg-gold hover:text-ink transition-colors"
              >
                ★ 克隆到我的关注
              </button>
              <button
                onClick={handleClearShared}
                className="px-4 py-2 border border-ink font-mono text-[11px] uppercase tracking-[0.18em] hover:bg-ink hover:text-paper transition-colors"
              >
                返回我的列表
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setShowAddInput((v) => !v)}
                className="px-4 py-2 border border-ink font-mono text-[11px] uppercase tracking-[0.18em] hover:bg-ink hover:text-paper transition-colors"
              >
                + 添加
              </button>
              <button
                onClick={handleCopyShare}
                disabled={tickers.length === 0}
                className="px-4 py-2 border border-ink font-mono text-[11px] uppercase tracking-[0.18em] hover:bg-ink hover:text-paper transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {showShareCopied ? '✓ 已复制' : '🔗 复制分享链接'}
              </button>
              <Link
                to="/portfolio"
                className="ml-auto px-4 py-2 font-mono text-[11px] uppercase tracking-[0.18em] text-mute hover:text-ink"
              >
                我的持仓 →
              </Link>
            </>
          )}
        </div>

        {showAddInput && !isShared && (
          <div className="mt-4 flex gap-2 items-center">
            <input
              type="text"
              autoFocus
              value={addText}
              onChange={(e) => setAddText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAdd()
                if (e.key === 'Escape') {
                  setAddText('')
                  setShowAddInput(false)
                }
              }}
              placeholder="输入 ticker，逗号或空格分隔，例如 AAOI, ALAB POET"
              className="flex-1 max-w-[480px] px-3 py-2 border border-ink font-mono text-[12px] bg-paper focus:outline-none focus:border-gold"
            />
            <button
              onClick={handleAdd}
              className="px-4 py-2 bg-ink text-paper font-mono text-[11px] uppercase tracking-[0.18em] hover:bg-gold hover:text-ink"
            >
              添加
            </button>
          </div>
        )}
      </section>

      {/* Empty state */}
      {rows.length === 0 && (
        <div className="py-24 text-center">
          <div className="font-serif text-[40px] font-black mb-3">空空如也</div>
          <div className="font-mono text-[12px] text-mute uppercase tracking-[0.15em] mb-6">
            {isShared
              ? '这个分享链接里没有股票'
              : '点详情页的 ☆ 关注按钮，或在上方输入框添加'}
          </div>
          <Link
            to="/"
            className="inline-block px-5 py-2 border border-ink font-mono text-[11px] uppercase tracking-[0.18em] hover:bg-ink hover:text-paper"
          >
            去今日颁奖看看 →
          </Link>
        </div>
      )}

      {/* Sort bar */}
      {rows.length > 0 && (
        <div className="mb-4 flex items-center gap-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute">
          <span>排序：</span>
          {(
            [
              ['order', '自定义'],
              ['pct_desc', '今日 ↓'],
              ['pct_asc', '今日 ↑'],
              ['awards_desc', '奖牌数 ↓'],
              ['ticker', 'A→Z'],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSortKey(key)}
              className={
                sortKey === key
                  ? 'text-ink font-medium border-b-2 border-gold pb-[2px]'
                  : 'text-mute hover:text-ink'
              }
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {/* Table */}
      {rows.length > 0 && (
        <div className="border border-ink">
          <table className="w-full font-mono text-[13px]">
            <thead>
              <tr className="border-b border-ink bg-ink text-paper text-[10px] uppercase tracking-[0.18em]">
                <th className="text-left px-3 py-2 font-medium">代码</th>
                <th className="text-left px-3 py-2 font-medium hidden sm:table-cell">名称</th>
                <th className="text-right px-3 py-2 font-medium">价格</th>
                <th className="text-right px-3 py-2 font-medium">今日</th>
                <th className="text-left px-3 py-2 font-medium hidden md:table-cell">档位</th>
                <th className="text-right px-3 py-2 font-medium hidden md:table-cell">奖牌</th>
                <th className="text-left px-3 py-2 font-medium hidden lg:table-cell">最佳奖</th>
                {!isShared && <th className="px-3 py-2 font-medium w-12"></th>}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr
                  key={r.ticker}
                  className="border-b border-ink/20 hover:bg-ink/[0.03]"
                >
                  <td className="px-3 py-3 font-bold">
                    <Link
                      to={`/stock/${r.ticker}`}
                      className="hover:text-gold-dim underline-offset-2 hover:underline"
                    >
                      {r.ticker}
                    </Link>
                  </td>
                  <td className="px-3 py-3 text-mute hidden sm:table-cell">
                    {r.found ? r.name : <span className="text-neg">不在数据池</span>}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums">
                    {r.close != null ? `$${r.close.toFixed(2)}` : '—'}
                  </td>
                  <td
                    className={`px-3 py-3 text-right tabular-nums font-bold ${
                      r.pct_change == null
                        ? 'text-mute'
                        : r.pct_change > 0
                        ? 'text-pos'
                        : r.pct_change < 0
                        ? 'text-neg'
                        : 'text-ink'
                    }`}
                  >
                    {r.pct_change != null ? formatPercent(r.pct_change) : '—'}
                  </td>
                  <td className="px-3 py-3 hidden md:table-cell">
                    {r.tier ? <TierBadge tier={r.tier} /> : <span className="text-mute">—</span>}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums hidden md:table-cell">
                    {r.awards_count ?? '—'}
                  </td>
                  <td className="px-3 py-3 hidden lg:table-cell text-gold-dim text-[12px]">
                    {r.best_award ?? '—'}
                  </td>
                  {!isShared && (
                    <td className="px-3 py-3 text-center">
                      <button
                        onClick={() => handleRemove(r.ticker)}
                        title="移出关注列表"
                        className="text-mute hover:text-neg text-[16px] leading-none"
                      >
                        ✕
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer hint */}
      <div className="mt-8 text-mute font-mono text-[11px] leading-relaxed">
        <p>· 关注列表只存 ticker，存在浏览器本地，不与持仓共用数据。</p>
        <p>· 通过 URL 即可分享：<code className="text-ink">/watch?w=AAOI,ALAB,POET</code></p>
        <p>· 想看持仓盈亏 / 成本价 / 占比 / 个股贡献，请去<Link to="/portfolio" className="text-ink underline">我的持仓</Link>。</p>
      </div>
    </div>
  )
}
