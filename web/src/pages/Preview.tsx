import { TierBadge } from '@/components/TierBadge'
import { AwardCard } from '@/components/AwardCard'
import { TierDistributionBar } from '@/components/TierDistributionBar'
import { StockChip } from '@/components/StockChip'
import { PersonaPill } from '@/components/PersonaPill'
import type { AwardGroup, TierName } from '@/types'

const TIERS: TierName[] = [
  '🔥 夯死了',
  '👑 顶级',
  '💪 人上人',
  '😐 NPC',
  '💩 拉完了',
  '☠️ 答辩',
]

const SAMPLE_AWARDS: AwardGroup[] = [
  {
    code: 'champion',
    name: '🏆 今日股王',
    description: '涨疯了，群里都在喊冲冲冲',
    winners: [
      { rank: 1, ticker: 'NVDA', metric: 12.34 },
      { rank: 2, ticker: 'AVGO', metric: 8.21 },
      { rank: 3, ticker: 'TSM', metric: 6.45 },
    ],
  },
  {
    code: 'daily_clown',
    name: '🤡 今日小丑',
    description: '一开盘就把昨天的脸打肿',
    winners: [
      { rank: 1, ticker: 'PLTR', metric: -9.87 },
      { rank: 2, ticker: 'COIN', metric: -7.23 },
      { rank: 3, ticker: 'TSLA', metric: -5.12 },
    ],
  },
  {
    code: 'pillar',
    name: '🏛️ 组合顶梁柱',
    description: '没它今天又得吃面',
    winners: [
      { rank: 1, ticker: 'AAPL', metric: 12345 },
      { rank: 2, ticker: 'MSFT', metric: 8421 },
      { rank: 3, ticker: 'GOOG', metric: 5230 },
    ],
  },
]

export default function Preview() {
  return (
    <div className="space-y-10">
      <section>
        <h2 className="zh mb-4">TierBadge</h2>
        <div className="flex flex-wrap gap-3">
          {TIERS.map((t) => (
            <TierBadge key={t} tier={t} size="lg" />
          ))}
        </div>
      </section>

      <section>
        <h2 className="zh mb-4">TierDistributionBar</h2>
        <TierDistributionBar
          distribution={{
            '🔥 夯死了': 5,
            '👑 顶级': 12,
            '💪 人上人': 22,
            '😐 NPC': 28,
            '💩 拉完了': 10,
            '☠️ 答辩': 4,
          }}
        />
      </section>

      <section>
        <h2 className="zh mb-4">StockChip + PersonaPill</h2>
        <div className="flex gap-6 items-start">
          <StockChip ticker="NVDA" persona="蒸蒸日上" />
          <StockChip ticker="TSLA" persona="财报戏精" />
          <StockChip ticker="AMD" />
          <PersonaPill persona="独立的 PersonaPill" />
        </div>
      </section>

      <section>
        <h2 className="zh mb-4">AwardCard</h2>
        <div className="columns-1 md:columns-2 lg:columns-3 gap-6">
          {SAMPLE_AWARDS.map((a, i) => (
            <AwardCard key={a.code} award={a} index={i} />
          ))}
        </div>
      </section>
    </div>
  )
}
