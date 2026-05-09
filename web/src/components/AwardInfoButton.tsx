import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getAwardMeta, type AwardMetaResponse } from '@/lib/api'

const CATEGORY_LABEL: Record<string, string> = {
  daily: '日度奖项',
  periodic: '周期奖项',
  earnings: '财报奖项',
  portfolio: '持仓奖项',
}

interface Props {
  /** Award code, e.g. 'daily_king' */
  code: string
  /** Joke/desc shown as native tooltip on the ⓘ glyph */
  shortDesc?: string
}

/**
 * `ⓘ` glyph + click-to-open modal. Native `title` provides a lightweight
 * tooltip on hover; the modal carries the full criterion + formula + history.
 */
export function AwardInfoButton({ code, shortDesc }: Props) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button
        type="button"
        aria-label="查看奖项规则"
        title={shortDesc ? `${shortDesc} · 点击查看评判标准` : '点击查看评判标准'}
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setOpen(true)
        }}
        className="inline-flex items-center justify-center w-[16px] h-[16px] rounded-full border border-mute text-mute font-mono text-[10px] leading-none hover:border-ink hover:text-ink transition-colors align-middle"
      >
        i
      </button>
      {open && <AwardModal code={code} onClose={() => setOpen(false)} />}
    </>
  )
}

function AwardModal({ code, onClose }: { code: string; onClose: () => void }) {
  // Lock scroll + ESC to close
  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = prev
      window.removeEventListener('keydown', onKey)
    }
  }, [onClose])

  const { data, isLoading, isError } = useQuery<AwardMetaResponse>({
    queryKey: ['awardMeta', code],
    queryFn: () => getAwardMeta(code),
  })

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 pb-8 px-4 overflow-y-auto"
      onClick={onClose}
      style={{ background: 'rgba(20, 18, 14, 0.55)' }}
    >
      <div
        className="w-full max-w-[640px] bg-paper border-[3px] border-ink shadow-none"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ── Masthead-style header ─────────────────────────────── */}
        <div className="px-7 pt-6 pb-5 border-b-[4px] border-ink">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <div className="kicker mb-2">
                {data?.meta.category
                  ? CATEGORY_LABEL[data.meta.category] || data.meta.category
                  : '奖项规则'}
                {data?.meta.code && (
                  <>
                    {' · '}
                    <span className="font-mono">{data.meta.code.toUpperCase()}</span>
                  </>
                )}
              </div>
              <h2 className="font-serif font-black text-[34px] leading-[1.05] tracking-[-0.01em]">
                {data?.meta.name || '—'}
              </h2>
              {data?.meta.desc && (
                <div className="mt-2 text-[13px] text-mute italic">
                  {data.meta.desc}
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="关闭"
              className="font-mono text-[18px] text-mute hover:text-ink leading-none px-1 shrink-0"
            >
              ✕
            </button>
          </div>
        </div>

        {/* ── Body ─────────────────────────────────────────────── */}
        <div className="px-7 py-6 space-y-6">
          {isLoading && <div className="kicker py-8 text-center">— 载入中 —</div>}
          {isError && (
            <div className="text-neg font-mono text-sm py-4">加载失败</div>
          )}
          {data && (
            <>
              {/* Criterion — plain language */}
              <section>
                <div className="kicker mb-2">评判标准</div>
                <p className="font-serif text-[16px] leading-[1.55] text-ink">
                  {data.meta.criterion || '—'}
                </p>
              </section>

              {/* Formula — technical */}
              {data.meta.formula && (
                <section>
                  <div className="kicker mb-2">计算公式</div>
                  <pre className="font-mono text-[12.5px] leading-[1.55] text-ink bg-paper-2 border border-rule px-3 py-2.5 whitespace-pre-wrap break-words">
                    {data.meta.formula}
                  </pre>
                </section>
              )}

              {/* Top holders — historical leaderboard */}
              <section>
                <div className="kicker mb-2 flex items-baseline justify-between">
                  <span>历史持有最多</span>
                  <span className="font-mono normal-case tracking-normal text-[10px]">
                    累计颁出 {data.total_awarded} 次
                  </span>
                </div>
                {data.top_holders.length === 0 ? (
                  <div className="text-mute text-[13px]">暂无历史数据</div>
                ) : (
                  <ul className="grid grid-cols-2 gap-x-6 gap-y-1.5">
                    {data.top_holders.map((h, i) => (
                      <li
                        key={h.ticker}
                        className="flex items-baseline justify-between border-b border-rule py-1"
                      >
                        <span className="flex items-baseline gap-2 min-w-0">
                          <span className="font-mono text-[10px] text-mute w-[14px] tabular-nums">
                            {String(i + 1).padStart(2, '0')}
                          </span>
                          <Link
                            to={`/stock/${h.ticker}`}
                            onClick={onClose}
                            className="font-mono font-bold text-[14px] hover:text-gold-dim"
                          >
                            {h.ticker}
                          </Link>
                        </span>
                        <span className="font-mono text-[12px] text-mute tabular-nums">
                          × {h.wins}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              {/* Last winner */}
              {data.last_winner && (
                <section>
                  <div className="kicker mb-2">最近一次获奖</div>
                  <div className="font-mono text-[13px]">
                    <span className="text-mute">{data.last_winner.period_key}</span>
                    <span className="mx-2 text-mute">·</span>
                    <Link
                      to={`/stock/${data.last_winner.ticker}`}
                      onClick={onClose}
                      className="font-bold hover:text-gold-dim"
                    >
                      {data.last_winner.ticker}
                    </Link>
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
