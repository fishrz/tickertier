// ── Static JSON fetcher ────────────────────────────────────────
// All data is fetched from /data/*.json (Vite public directory).
// No backend / API server needed — purely static deployment.

import type {
  AwardsTodayResponse,
  HealthResponse,
  PortfolioToday,
  PortfolioPosition,
  StockDetail,
  LeaderboardEntry,
  AwardTopEntry,
  RaceResponse,
} from '@/types'

// ── Module-level JSON cache ────────────────────────────────────
// Fetch each URL once per page load; subsequent calls return the
// cached promise.  React Query adds a second layer of dedup on top.

const _cache = new Map<string, Promise<any>>()

function fetchJSON<T>(path: string): Promise<T> {
  if (!_cache.has(path)) {
    _cache.set(
      path,
      fetch(path).then((r) => {
        if (!r.ok) throw new Error(`Failed to load ${path}: ${r.status}`)
        return r.json()
      }),
    )
  }
  return _cache.get(path)!
}

// ── Raw JSON shapes (match the static export files) ────────────

interface AggregatedMedal {
  code: string
  name: string
  count: number
  gold: number
  silver: number
  bronze: number
  best_rank: number | null
  latest_period_key: string | null
  period: string | null
}

export interface StockRow {
  ticker: string
  name: string
  theme: string | null
  close: number | null
  pct_change: number | null
  intraday_amp: number | null
  vol_ratio_20: number | null
  tier: string | null
  awards_count: number
  persona: string | null
  medal_history: AggregatedMedal[]
  tier_distribution: Record<string, number>
  recent_30d: { date: string; close: number | null; pct_change: number | null; tier: string | null }[]
}

interface TiersFile {
  date: string | null
  tiers: { ticker: string; tier: string; score: number; rank_pct: number }[]
}

interface HallFile {
  all_time: { ticker: string; gold: number; silver: number; bronze: number; total: number; persona: string | null }[]
  by_period: Record<string, { ticker: string; gold: number; silver: number; bronze: number; total: number }[]>
  windows: Record<string, Record<string, { ticker: string; gold: number; silver: number; bronze: number; total: number; persona: string | null }[]>>
  by_award_code: Record<string, { ticker: string; gold: number; silver: number; bronze: number; total: number; persona: string | null }[]>
  by_award_code_windows?: Record<string, Record<string, { ticker: string; gold: number; silver: number; bronze: number; total: number; persona: string | null }[]>>
}

interface RaceGranularity {
  period: string
  frames: { date: string; entries: { ticker: string; value: number; rank: number }[] }[]
}

interface RaceFile {
  daily: RaceGranularity
  weekly: RaceGranularity
  monthly: RaceGranularity
  quarterly: RaceGranularity
  yearly: RaceGranularity
}

interface MetaFile {
  last_updated: string
  universe: number
  awards: number
  data_from: string | null
  data_to: string | null
}

// ── Exported interfaces (kept for backwards compat) ────────────

export interface StatsResponse {
  universe: number
  awards: number
  medals_awarded: number
  data_from: string | null
  data_to: string | null
}

export interface RelatedStock {
  ticker: string
  persona: string | null
  theme: string
}
export interface RelatedResponse {
  ticker: string
  self_persona: string | null
  self_theme: string
  same_persona: RelatedStock[]
  same_theme: RelatedStock[]
}

export interface AwardMeta {
  code: string
  name: string
  desc: string
  category: string
  unit: string
  criterion: string
  formula: string
}

export interface AwardMetaResponse {
  meta: AwardMeta
  top_holders: { ticker: string; wins: number }[]
  total_awarded: number
  last_winner: { period_key: string; ticker: string; value: number | null } | null
}

// ── Award metadata (mirrors api/awards_meta.py) ───────────────

const AWARD_META_MAP: Record<string, AwardMeta> = {
  daily_king: {
    code: 'daily_king', name: '🏆 今日股王', desc: '夯到飞起',
    category: 'daily', unit: 'pct',
    criterion: '当天涨幅最大的那只股，简单粗暴。',
    formula: 'argmax (close − prev_close) / prev_close × 100，排除 QQQ 等基准。Top 3 上榜。',
  },
  daily_clown: {
    code: 'daily_clown', name: '💩 今日答辩', desc: '建议退市',
    category: 'daily', unit: 'pct',
    criterion: '当天跌得最惨的股，今天它最丢人。',
    formula: 'argmin (close − prev_close) / prev_close × 100，排除基准。Top 3 上榜。',
  },
  roller_coaster: {
    code: 'roller_coaster', name: '🎢 过山车之王', desc: '早上人上人，下午拉完了',
    category: 'daily', unit: 'amp',
    criterion: '当天日内振幅最大的股，K 线像心电图。',
    formula: 'argmax (high − low) / prev_close × 100。',
  },
  oscar: {
    code: 'oscar', name: '🎭 影帝奖', desc: '开盘装大佬，收盘装死',
    category: 'daily', unit: 'pct',
    criterion: '开盘高开高走，收盘原形毕露。装得最像的就是影帝。',
    formula: '在 gap > 0 的股票里，argmin fade，其中 fade = (close − high) / high × 100。',
  },
  comeback: {
    code: 'comeback', name: '🪄 绝地翻身奖', desc: '主打一个不装了',
    category: 'daily', unit: 'pct',
    criterion: '盘中触底之后猛拉，最终收涨。主打一个绝地反击。',
    formula: '在 pct_change > 0 的股票里，argmax rebound = (close − low) / low × 100。',
  },
  npc_god: {
    code: 'npc_god', name: '💤 NPC 之光', desc: '在的，活着，不动',
    category: 'daily', unit: 'amp',
    criterion: '当天波澜不惊+成交量低迷的股，全场最 NPC。',
    formula: 'vol_ratio_20 < 0.7 的股里，argmin intraday_amp。',
  },
  pump_army: {
    code: 'pump_army', name: '📈 暴兵奖', desc: '主力进场了家人们',
    category: 'daily', unit: 'count',
    criterion: '上涨日里量能爆发最猛的，疑似主力进场。',
    formula: '在 pct_change > 0 的股票里，argmax vol_ratio_20 = volume / 20日均量。',
  },
  tank: {
    code: 'tank', name: '🛡️ 抗揍奖', desc: '大盘崩我不崩，反向 indicator 王',
    category: 'daily', unit: 'pct',
    criterion: '大盘明显下跌的日子里，跌得最少甚至上涨的那只。',
    formula: '前提：QQQ pct_change ≤ −0.5%。取 argmax(ticker.pct_change − QQQ.pct_change)。',
  },
  reverse_idx: {
    code: 'reverse_idx', name: '🪦 反指奖', desc: '陪跑十级运动员',
    category: 'periodic', unit: 'pct',
    criterion: '周期内跟 QQQ 走势最反着来的股，标准的反指。',
    formula: '按日级 pct_change 与 QQQ 计算 Pearson 相关系数，取最负的。',
  },
  steady_grind: {
    code: 'steady_grind', name: '🐢 细水长流奖', desc: '老老实实赚钱',
    category: 'periodic', unit: 'pct',
    criterion: '周期内涨幅稳健、波动又小的股。不靠暴涨，靠长跑。',
    formula: '周期累计收益 / 日级收益标准差（年化），即 Sharpe-like ratio。',
  },
  gambler: {
    code: 'gambler', name: '🎰 赌狗之友奖', desc: '心脏起搏器赞助商',
    category: 'periodic', unit: 'amp',
    criterion: '周期内累计振幅最大的股，最适合心跳爱好者。',
    formula: 'Σ intraday_amp_t over period，取 sum 最大的 ticker。',
  },
  workhorse: {
    code: 'workhorse', name: '🏅 劳模奖', desc: '奖项收割机',
    category: 'periodic', unit: 'medals',
    criterion: '周期内拿过最多日度金牌的股，奖项含金量直接拉满。',
    formula: 'count(awards where rank=1 AND period=\'D\') GROUP BY ticker，取最高。',
  },
  silver_curse: {
    code: 'silver_curse', name: '🪑 万年老二奖', desc: '一人之下万人之上的疲惫感',
    category: 'periodic', unit: 'medals',
    criterion: '周期内拿了最多次「亚军」的股。永远第二，痛并快乐。',
    formula: 'count(awards where rank=2 AND period=\'D\') GROUP BY ticker。',
  },
  earnings_god: {
    code: 'earnings_god', name: '💼 财报封神', desc: '数字会自己说话',
    category: 'earnings', unit: 'pct',
    criterion: '财报次日跳得最猛的股，业绩直接干到位。',
    formula: 'next_day_pct = (T+1 close − T close) / T close × 100，取最大值。',
  },
  earnings_clown: {
    code: 'earnings_clown', name: '💼 财报现形', desc: '原形毕露',
    category: 'earnings', unit: 'pct',
    criterion: '财报次日跌得最惨的股，业绩直接破防。',
    formula: 'next_day_pct = (T+1 close − T close) / T close × 100，取最小值。',
  },
  pillar: {
    code: 'pillar', name: '💰 顶梁柱奖', desc: '全家就指望你了',
    category: 'portfolio', unit: 'amount',
    criterion: '持仓中按真实仓位加权后，对账户当日盈亏贡献最大的股。',
    formula: 'argmax (shares × close × pct_change / 100)。',
  },
  traitor: {
    code: 'traitor', name: '🩸 拖后腿奖', desc: '建议清仓谢罪',
    category: 'portfolio', unit: 'amount',
    criterion: '持仓中按真实仓位加权后，对账户拖累最大的股。',
    formula: 'argmin (shares × close × pct_change / 100)。',
  },
  cash_king: {
    code: 'cash_king', name: '💸 钞能力之王', desc: '实打实赚到钱的那个',
    category: 'portfolio', unit: 'amount',
    criterion: '持仓中累计浮盈金额最大的股。',
    formula: 'argmax (last_close − avg_cost) × shares，仅取浮盈 > 0 的持仓。',
  },
  tear_jerker: {
    code: 'tear_jerker', name: '😭 我的眼泪奖', desc: '套牢套到亲妈不认',
    category: 'portfolio', unit: 'amount',
    criterion: '持仓中累计浮亏金额最深的股。看一次哭一次。',
    formula: 'argmin (last_close − avg_cost) × shares，仅取浮亏 < 0。',
  },
  big_position: {
    code: 'big_position', name: '👑 仓位之王', desc: '你就是我的全部',
    category: 'portfolio', unit: 'pct',
    criterion: '占整个账户市值比例最高的持仓。',
    formula: 'argmax (shares × last_close) / Σ(shares × last_close) × 100。',
  },
  buy_low: {
    code: 'buy_low', name: '🧠 人间清醒奖', desc: '买在脚踝上的天选之子',
    category: 'portfolio', unit: 'pct',
    criterion: '成本价相对当前价折扣最大的持仓。',
    formula: 'argmax (last_close − avg_cost) / avg_cost × 100，仅取浮盈 > 0。',
  },
}

// ── Shared data helpers ────────────────────────────────────────

let _stocksPromise: Promise<StockRow[]> | null = null
export function getStocks(): Promise<StockRow[]> {
  if (!_stocksPromise) _stocksPromise = fetchJSON<StockRow[]>('/data/stocks.json')
  return _stocksPromise
}

// ── API functions ──────────────────────────────────────────────

export async function getStats(): Promise<StatsResponse> {
  const m = await fetchJSON<MetaFile>('/data/meta.json')
  return {
    universe: m.universe,
    awards: m.awards,
    medals_awarded: m.awards,
    data_from: m.data_from,
    data_to: m.data_to,
  }
}

export async function getHealth(): Promise<HealthResponse> {
  try {
    const m = await fetchJSON<MetaFile>('/data/meta.json')
    return { status: 'ok', db_path: '', as_of: m.last_updated ?? '' }
  } catch {
    return { status: 'offline', db_path: '', as_of: '' }
  }
}

export async function getAwardsToday(): Promise<AwardsTodayResponse> {
  return fetchJSON('/data/today.json')
}

export async function getTodayTiers(): Promise<{ date: string; members: Record<string, string[]> }> {
  const file = await fetchJSON<TiersFile>('/data/tiers.json')
  const members: Record<string, string[]> = {}
  for (const r of file.tiers) {
    if (!members[r.tier]) members[r.tier] = []
    members[r.tier].push(r.ticker)
  }
  return { date: file.date ?? '', members }
}

export async function getAwardsPeriod(_period: string, _key: string) {
  // Not available in static data
  return null
}

export async function getLeaderboard(
  params: { window?: string; granularity?: string; limit?: number } = {},
): Promise<LeaderboardEntry[]> {
  const file = await fetchJSON<HallFile>('/data/hall.json')
  const { window = 'all', granularity = 'ALL', limit = 20 } = params

  let rows: { ticker: string; gold: number; silver: number; bronze: number; total: number; persona?: string | null }[] = []

  // Prefer the windows × granularity matrix
  const winBucket = file.windows?.[window]
  if (winBucket) {
    rows = winBucket[granularity] ?? winBucket.ALL ?? []
  }
  // Fallback to legacy by_period (case-insensitive partial match)
  if (rows.length === 0 && file.by_period && file.by_period[window]) {
    rows = file.by_period[window]
  }
  // Last resort: all-time
  if (rows.length === 0) {
    rows = file.all_time
  }

  return rows.slice(0, limit).map((r) => ({
    ticker: r.ticker,
    persona: r.persona ?? null,
    gold: r.gold,
    silver: r.silver,
    bronze: r.bronze,
    total: r.total,
  }))
}

export async function getAwardTopByCode(
  code: string,
  n = 3,
  win: string = 'all',
): Promise<AwardTopEntry[]> {
  const file = await fetchJSON<HallFile>('/data/hall.json')
  const windowed = file.by_award_code_windows?.[win]?.[code]
  const rows = windowed ?? file.by_award_code?.[code] ?? []
  return rows.slice(0, n).map((r) => ({
    ticker: r.ticker,
    total_wins: r.total,
    gold: r.gold,
    silver: r.silver,
    bronze: r.bronze,
  }))
}

export async function getRace(
  metric = 'cum_return',
  options: { from?: string; to?: string; granularity?: string } = {},
): Promise<RaceResponse> {
  const file = await fetchJSON<RaceFile>('/data/race.json')

  // Map requested granularity to file key
  const granMap: Record<string, keyof RaceFile> = {
    D: 'daily', daily: 'daily',
    W: 'weekly', weekly: 'weekly',
    M: 'monthly', monthly: 'monthly',
    Q: 'quarterly', quarterly: 'quarterly',
    Y: 'yearly', yearly: 'yearly',
  }

  // If caller explicitly passed granularity, use it.
  // Otherwise auto-pick from the date span: ≤45d=D, ≤200d=W, ≤800d=M, ≤2000d=Q, else Y.
  let key: keyof RaceFile
  if (options.granularity && granMap[options.granularity]) {
    key = granMap[options.granularity]
  } else if (options.from && options.to) {
    const span = (new Date(options.to).getTime() - new Date(options.from).getTime()) / 86400000
    if (span <= 45) key = 'daily'
    else if (span <= 200) key = 'weekly'
    else if (span <= 800) key = 'monthly'
    else if (span <= 2000) key = 'quarterly'
    else key = 'yearly'
  } else {
    key = 'monthly'
  }
  const data = file[key]

  // Filter frames by date range if requested
  let frames = data.frames
  if (options.from || options.to) {
    frames = frames.filter((f) => {
      if (options.from && f.date < options.from) return false
      if (options.to && f.date > options.to) return false
      return true
    })
  }

  return { metric, period: data.period, frames }
}

export async function getPortfolioToday(): Promise<PortfolioToday> {
  // Read positions from localStorage; seed from static file if empty
  const STORAGE_KEY = 'tickertier_portfolio'
  let userPositions: { ticker: string; shares: number; avg_cost: number }[] = []
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) userPositions = JSON.parse(raw)
  } catch {
    // ignore
  }

  if (userPositions.length === 0) {
    try {
      const portfolioFile = await fetchJSON<{ positions: { ticker: string; shares: number; avg_cost: number }[] }>('/data/portfolio_positions.json')
      if (portfolioFile?.positions?.length > 0) {
        userPositions = portfolioFile.positions.map((p) => ({
          ticker: p.ticker,
          shares: p.shares,
          avg_cost: p.avg_cost,
        }))
        // Seed localStorage for future loads
        localStorage.setItem(STORAGE_KEY, JSON.stringify(userPositions))
      }
    } catch {
      // File not available — that's fine
    }
  }

  const stocks = await getStocks()
  const stockMap = new Map(stocks.map((s) => [s.ticker, s]))

  const rawPositions = userPositions
    .map((p) => {
      const stock = stockMap.get(p.ticker)
      if (!stock || stock.close == null) return null
      const last_close = stock.close
      const pct_change = stock.pct_change ?? 0
      const market_value = p.shares * last_close
      const unrealized_pnl = (last_close - p.avg_cost) * p.shares
      // Approximate today P&L: shares × close × pct_change
      // pct_change is a fraction (e.g. 0.0654 = 6.54%)
      const today_pnl = p.shares * last_close * pct_change
      const today_pct = pct_change
      return {
        ticker: p.ticker,
        shares: p.shares,
        avg_cost: p.avg_cost,
        last_close,
        market_value,
        unrealized_pnl,
        today_pnl,
        today_pct,
        tier_today: stock.tier ?? null,
        lottery: false as boolean | undefined,
      }
    })
    .filter((p): p is NonNullable<typeof p> => p !== null)

  const positions = rawPositions as PortfolioPosition[]

  const total_market_value = positions.reduce((s, p) => s + p.market_value, 0)
  const total_unrealized_pnl = positions.reduce((s, p) => s + p.unrealized_pnl, 0)
  const today_pnl = positions.reduce((s, p) => s + p.today_pnl, 0)

  // Mark lottery positions (< 0.5% of portfolio)
  for (const p of positions) {
    p.lottery = total_market_value > 0 && (p.market_value / total_market_value) < 0.005
  }

  // Compute highlights (non-lottery positions only)
  type HL = { ticker: string; contribution: number } | null
  const live = positions.filter((p) => !p.lottery)

  function argmax(arr: PortfolioPosition[], fn: (p: PortfolioPosition) => number): HL {
    if (arr.length === 0) return null
    let best = arr[0]
    let bestVal = fn(best)
    for (let i = 1; i < arr.length; i++) {
      const v = fn(arr[i])
      if (v > bestVal) { best = arr[i]; bestVal = v }
    }
    return { ticker: best.ticker, contribution: bestVal }
  }

  function argmin(arr: PortfolioPosition[], fn: (p: PortfolioPosition) => number): HL {
    if (arr.length === 0) return null
    let best = arr[0]
    let bestVal = fn(best)
    for (let i = 1; i < arr.length; i++) {
      const v = fn(arr[i])
      if (v < bestVal) { best = arr[i]; bestVal = v }
    }
    return { ticker: best.ticker, contribution: bestVal }
  }

  const pillar: HL = argmax(live, (p) => p.today_pnl)
  const traitor: HL = argmin(live, (p) => p.today_pnl)
  const cash_king: HL = argmax(
    live.filter((p) => p.unrealized_pnl > 0),
    (p) => p.unrealized_pnl,
  )
  const tear_jerker: HL = argmin(
    live.filter((p) => p.unrealized_pnl < 0),
    (p) => p.unrealized_pnl,
  )
  const big_position: HL = argmax(live, (p) =>
    total_market_value > 0 ? (p.market_value / total_market_value) * 100 : 0,
  )
  const buy_low: HL = argmax(
    live.filter((p) => p.unrealized_pnl > 0),
    (p) => ((p.last_close - p.avg_cost) / p.avg_cost) * 100,
  )

  const highlights: PortfolioToday['highlights'] = {
    pillar,
    traitor,
    cash_king,
    tear_jerker,
    big_position,
    buy_low,
  }

  return {
    as_of: '',
    total_market_value,
    total_unrealized_pnl,
    today_pnl,
    pillar,
    traitor,
    highlights,
    positions,
  }
}

export async function getStock(ticker: string): Promise<StockDetail> {
  const stocks = await getStocks()
  const stock = stocks.find((s) => s.ticker === ticker)
  if (!stock) throw new Error(`Stock ${ticker} not found`)

  // medal_history is now pre-aggregated per award_code in stocks.json
  // (one entry per award code, with gold/silver/bronze counts).
  const total_gold = stock.medal_history.reduce((s, m) => s + m.gold, 0)
  const total_silver = stock.medal_history.reduce((s, m) => s + m.silver, 0)
  const total_bronze = stock.medal_history.reduce((s, m) => s + m.bronze, 0)

  return {
    ticker: stock.ticker,
    name: stock.name,
    theme: stock.theme,
    persona: stock.persona,
    medal_count: {
      gold: total_gold,
      silver: total_silver,
      bronze: total_bronze,
      total: stock.awards_count,
    },
    medal_history: stock.medal_history.map((m) => ({
      code: m.code,
      name: m.name,
      count: m.count,
      latest_date: m.latest_period_key,
      best_rank: m.best_rank,
    })),
    tier_distribution: stock.tier_distribution,
    last_close: stock.close,
    last_pct_change: stock.pct_change,
    recent_30d: stock.recent_30d
      .filter((r) => r.close != null)
      .map((r) => ({
        date: r.date,
        close: r.close as number,
        pct_change: r.pct_change ?? undefined,
        tier: r.tier ?? undefined,
      })),
    streak_top_tier_days: (stock as any).streak_top_tier_days ?? 0,
    streak_in_awards_days: (stock as any).streak_in_awards_days ?? 0,
  }
}

export async function getStockMedals(_ticker: string, _period = 'Y') {
  // Per-period medal breakdown not exported.
  // The aggregated counts live on getStock().medal_history.
  return []
}

export async function getStockRelated(ticker: string, limit = 8): Promise<RelatedResponse> {
  const stocks = await getStocks()
  const stock = stocks.find((s) => s.ticker === ticker)
  const self_persona = stock?.persona ?? null
  const self_theme = stock?.theme ?? ''

  const same_persona: RelatedStock[] = stocks
    .filter((s) => s.ticker !== ticker && s.persona === self_persona && self_persona != null)
    .slice(0, limit)
    .map((s) => ({ ticker: s.ticker, persona: s.persona, theme: s.theme ?? '' }))

  const same_theme: RelatedStock[] = stocks
    .filter((s) => s.ticker !== ticker && s.theme && s.theme === self_theme)
    .slice(0, limit)
    .map((s) => ({ ticker: s.ticker, persona: s.persona, theme: s.theme ?? '' }))

  return { ticker, self_persona, self_theme, same_persona, same_theme }
}

export async function getAwardMeta(code: string): Promise<AwardMetaResponse> {
  const meta = AWARD_META_MAP[code]
  if (!meta) {
    throw new Error(`Unknown award: ${code}`)
  }
  // Pull top holders + total awarded from hall.json (built nightly by export_json.py)
  let top_holders: { ticker: string; wins: number }[] = []
  let total_awarded = 0
  let last_winner: AwardMetaResponse['last_winner'] = null
  try {
    const hall = await fetchJSON<HallFile>('/data/hall.json')
    const rows = hall.by_award_code?.[code] ?? []
    top_holders = rows.slice(0, 8).map((r) => ({ ticker: r.ticker, wins: r.total }))
    total_awarded = rows.reduce((a, r) => a + r.total, 0)
  } catch {
    // hall.json may not be available in some environments; gracefully degrade
  }
  // Last winner from today.json if this award appears in today's slate
  try {
    const today = await fetchJSON<{ date: string; awards: { code: string; winners: { ticker: string }[] }[] }>('/data/today.json')
    const a = today.awards?.find((x) => x.code === code)
    if (a?.winners?.[0]?.ticker) {
      last_winner = { period_key: today.date, ticker: a.winners[0].ticker, value: null }
    }
  } catch {
    // ignore
  }
  return {
    meta,
    top_holders,
    total_awarded,
    last_winner,
  }
}
