import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, LayoutGroup } from 'framer-motion'
import { getRace } from '@/lib/api'
import { Hero } from '@/components/Hero'
import type { RaceResponse, RaceEntry } from '@/types'

// ── Metric config ──────────────────────────────────────────────
const METRICS = [
  { key: 'cum_return', label: '累计涨幅' },
  { key: 'medal_count', label: '奖牌榜' },
] as const

// ── Range config — selects from/to window passed to API.
// API auto-picks granularity from the date span: ≤180d=D, ≤730d=W, else M.
// So 1月→daily, 1季→daily, 1年→weekly, 全部→monthly.
const RANGES = [
  { key: '1m', label: '近1月', days: 30 },
  { key: '1q', label: '近1季', days: 92 },
  { key: '1y', label: '近1年', days: 365 },
  { key: 'all', label: '全部', days: null }, // null = no from/to filter
] as const

const TOP_N = 15
const BASE_INTERVAL_MS = 240 // ~4fps base — readable at 1x; 0.5x for slow study, 2x for skim

// Stable per-ticker color from a curated 8-slot palette.
// Stays in the newspaper-black + gold + earth-tone family — no rainbow.
const PALETTE = [
  'var(--gold)',          // 旧奖杯金
  'var(--ink)',           // 报纸黑
  '#7d6a3a',              // 暗金/橄榄
  '#3f5840',              // 深森林绿
  '#7a3b2e',              // 干血色 / 砖红
  '#4a4a4a',              // 中灰
  '#8a6a4a',              // 铜
  '#2c4257',              // 深石板蓝
] as const

function tickerColor(t: string): string {
  let h = 0
  for (let i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) >>> 0
  return PALETTE[h % PALETTE.length]
}

// ── Helpers ─────────────────────────────────────────────────────
function formatMetric(metric: string, v: number): string {
  if (metric === 'cum_return') {
    const sign = v > 0 ? '+' : ''
    return `${sign}${v.toFixed(2)}%`
  }
  // medal_count — plain number, no emoji per visual language
  return `${Math.round(v)}`
}

function formatDate(d: string, period: string): string {
  const dt = new Date(d)
  if (period === 'M') return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}`
  if (period === 'Q') {
    const q = Math.floor(dt.getMonth() / 3) + 1
    return `${dt.getFullYear()} Q${q}`
  }
  return `${dt.getMonth() + 1}/${dt.getDate()}`
}

function formatDateFull(d: string): string {
  const dt = new Date(d)
  return `${dt.getFullYear()}.${String(dt.getMonth() + 1).padStart(2, '0')}.${String(dt.getDate()).padStart(2, '0')}`
}

// ── Bar component ───────────────────────────────────────────────
function RaceBar({
  entry,
  maxVal,
  metric,
  idx,
  intervalMs,
}: {
  entry: RaceEntry
  maxVal: number
  metric: string
  idx: number
  intervalMs: number
}) {
  const pct = maxVal > 0 ? Math.max((Math.abs(entry.value) / maxVal) * 100, 2) : 2
  // Match transition duration to frame interval so the bar/row glides
  // smoothly into place between ticks instead of snapping.
  const moveDur = Math.max(intervalMs / 1000, 0.18)

  return (
    <motion.div
      layout
      initial={{ opacity: 0.6 }}
      animate={{ opacity: 1 }}
      transition={{
        layout: { type: 'tween', ease: 'easeInOut', duration: moveDur },
        opacity: { duration: 0.2 },
      }}
      className="flex items-center gap-3 mb-[6px]"
      style={{ height: 32 }}
    >
      {/* Rank */}
      <span className="w-5 text-right font-mono text-[11px] text-mute tabular-nums shrink-0">
        {idx + 1}
      </span>
      {/* Ticker */}
      <span className="w-14 font-mono font-medium text-[13px] tracking-wide shrink-0">
        {entry.ticker}
      </span>
      {/* Bar track */}
      <div className="flex-1 relative h-full">
        <motion.div
          layout
          className="absolute inset-y-0 left-0"
          style={{ width: `${pct}%`, background: tickerColor(entry.ticker) }}
          transition={{ type: 'tween', ease: 'easeInOut', duration: moveDur }}
        />
      </div>
      {/* Value */}
      <span
        className={`w-[90px] text-right font-mono text-[13px] font-medium tabular-nums shrink-0 ${
          entry.value > 0 ? 'text-pos' : entry.value < 0 ? 'text-neg' : 'text-mute'
        }`}
      >
        {formatMetric(metric, entry.value)}
      </span>
    </motion.div>
  )
}

// ── Main page ───────────────────────────────────────────────────
export default function Race() {
  const [metricKey, setMetricKey] = useState<string>('cum_return')
  const [rangeKey, setRangeKey] = useState<string>('1y')
  const [frameIdx, setFrameIdx] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [speed, setSpeed] = useState(1)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Compute from/to from range key. Today is the upper bound.
  const { fromIso, toIso } = useMemo(() => {
    const cfg = RANGES.find((r) => r.key === rangeKey)
    if (!cfg || cfg.days == null) return { fromIso: undefined, toIso: undefined }
    const today = new Date()
    const from = new Date(today)
    from.setDate(from.getDate() - cfg.days)
    const fmt = (d: Date) =>
      `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    return { fromIso: fmt(from), toIso: fmt(today) }
  }, [rangeKey])

  const { data, isLoading, isError, error } = useQuery<RaceResponse>({
    queryKey: ['race', metricKey, rangeKey],
    queryFn: () =>
      getRace(metricKey === 'medal_count' ? 'medals' : 'cum_return', {
        from: fromIso,
        to: toIso,
      }),
  })

  const frames = data?.frames ?? []
  const granularity = data?.period ?? 'D' // server-decided
  const currentFrame = frames[frameIdx] ?? null
  const intervalMs = BASE_INTERVAL_MS / speed
  const maxVal = useMemo(() => {
    if (!currentFrame) return 100
    const vals = currentFrame.entries.map((e) => Math.abs(e.value))
    return Math.max(...vals, 1)
  }, [currentFrame])

  // ── Playback ──────────────────────────────────────────────────
  const tick = useCallback(() => {
    setFrameIdx((prev) => {
      if (prev >= frames.length - 1) {
        setPlaying(false)
        return prev
      }
      return prev + 1
    })
  }, [frames.length])

  useEffect(() => {
    if (!playing || frames.length === 0) {
      if (intervalRef.current) clearInterval(intervalRef.current)
      return
    }
    const ms = BASE_INTERVAL_MS / speed
    intervalRef.current = setInterval(tick, ms)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [playing, speed, tick, frames.length])

  // Auto-play on data arrival
  useEffect(() => {
    if (frames.length > 0 && frameIdx === 0 && !playing) {
      setPlaying(true)
    }
  }, [frames.length]) // eslint-disable-line react-hooks/exhaustive-deps

  // Reset frame when data changes
  useEffect(() => {
    setFrameIdx(0)
    setPlaying(true)
  }, [metricKey, rangeKey]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Handlers ───────────────────────────────────────────────────
  const handlePlayPause = () => {
    if (!playing && frameIdx >= frames.length - 1) {
      setFrameIdx(0)
      setPlaying(true)
    } else {
      setPlaying(!playing)
    }
  }

  const handleSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const idx = parseInt(e.target.value, 10)
    setFrameIdx(idx)
    setPlaying(false)
  }

  if (isLoading) {
    return <div className="py-32 text-center kicker">— 载入中 —</div>
  }

  if (isError || !data) {
    return (
      <div className="py-32 text-center text-neg font-mono text-sm">
        加载失败: {(error as Error)?.message || '未知错误'}
      </div>
    )
  }

  return (
    <>
      <Hero
        title={
          <>
            <span className="block">年度</span>
            <span className="block">
              <em className="not-italic font-bold text-gold-dim italic">颁奖</em>典礼
            </span>
          </>
        }
        subtitle="排名变迁 · 81支AI基建标的实况竞速"
      />

      {/* ── Mode tabs ────────────────────────────────────────────── */}
      <div className="flex gap-6 border-b-[4px] border-ink">
        {METRICS.map((m) => (
          <button
            key={m.key}
            onClick={() => setMetricKey(m.key)}
            className={`pb-3 font-serif text-[20px] tracking-tight transition-colors ${
              metricKey === m.key
                ? 'text-ink font-black border-b-2 border-gold'
                : 'text-mute hover:text-ink'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* ── Controls ──────────────────────────────────────────────── */}
      <div className="flex items-center gap-6 py-5 border-b border-ink">
        {/* Play / Pause */}
        <button
          onClick={handlePlayPause}
          className="font-mono text-[11px] uppercase tracking-[0.15em] px-4 py-2 border border-ink bg-ink text-paper hover:bg-paper hover:text-ink transition-colors"
        >
          {playing ? '⏸ 暂停' : frameIdx >= frames.length - 1 ? '▶ 重播' : '▶ 播放'}
        </button>

        {/* Speed */}
        <div className="flex gap-2">
          {[0.5, 1, 2].map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={`font-mono text-[11px] px-2 py-1 border transition-colors ${
                speed === s
                  ? 'border-ink bg-ink text-paper'
                  : 'border-ink text-mute hover:bg-paper-2'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>

        {/* Range selector */}
        <div className="flex gap-2 ml-4">
          {RANGES.map((r) => (
            <button
              key={r.key}
              onClick={() => setRangeKey(r.key)}
              className={`font-mono text-[11px] px-2 py-1 border transition-colors ${
                rangeKey === r.key
                  ? 'border-ink bg-ink text-paper'
                  : 'border-ink text-mute hover:bg-paper-2'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>

        {/* Current date — big mono display */}
        <div className="ml-auto font-mono text-[28px] tracking-[-0.02em] text-ink font-medium tabular-nums">
          {currentFrame ? formatDateFull(currentFrame.date) : '—'}
        </div>
      </div>

      {/* ── Slider ───────────────────────────────────────────────── */}
      <div className="py-3 border-b border-ink">
        <input
          type="range"
          min={0}
          max={Math.max(frames.length - 1, 0)}
          value={frameIdx}
          onChange={handleSlider}
          className="w-full accent-gold h-[6px] cursor-pointer"
          style={{ accentColor: 'var(--gold)' }}
        />
        <div className="flex justify-between font-mono text-[10px] text-mute mt-1">
          <span>{frames.length > 0 ? formatDate(frames[0].date, granularity) : ''}</span>
          <span>
            {frames.length > 0 ? formatDate(frames[frames.length - 1].date, granularity) : ''}
          </span>
        </div>
      </div>

      {/* ── Race chart ────────────────────────────────────────────── */}
      <section className="pt-8 pb-16">
        {currentFrame ? (
          <LayoutGroup>
            <div className="flex flex-col">
              {currentFrame.entries.slice(0, TOP_N).map((entry, idx) => (
                <RaceBar
                  key={entry.ticker}
                  entry={entry}
                  maxVal={maxVal}
                  metric={metricKey === 'medal_count' ? 'medals' : metricKey}
                  idx={idx}
                  intervalMs={intervalMs}
                />
              ))}
            </div>
          </LayoutGroup>
        ) : (
          <div className="py-12 text-center kicker">暂无数据</div>
        )}
      </section>
    </>
  )
}