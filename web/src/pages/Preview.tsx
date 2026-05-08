import { TierBadge } from '@/components/TierBadge'
import { StockChip } from '@/components/StockChip'
import { PersonaPill } from '@/components/PersonaPill'
import { AwardCard } from '@/components/AwardCard'
import { TierBar } from '@/components/TierBar'
import { TierTable } from '@/components/TierTable'
import { Hero } from '@/components/Hero'

// Component QA / 设计语言验收页
const SAMPLE_AWARD = {
  code: 'stock_king',
  name: '🏆 今日股王',
  description: '今日涨幅最猛的三位',
  winners: [
    { rank: 1, ticker: 'AKAM', metric: 0.1659 },
    { rank: 2, ticker: 'NVDA', metric: 0.0742 },
    { rank: 3, ticker: 'AVGO', metric: 0.0521 },
  ],
}
const SAMPLE_BAD = {
  code: 'crap',
  name: '💩 今日答辩',
  description: '别看了，就是它',
  winners: [
    { rank: 1, ticker: 'CRWV', metric: -0.1117 },
    { rank: 2, ticker: 'WOLF', metric: -0.0683 },
    { rank: 3, ticker: 'VRT', metric: -0.0411 },
  ],
}
const SAMPLE_TIERS = {
  '🔥 夯死了': ['AKAM', 'AVGO', 'NVDA', 'TSM', 'MU'],
  '👑 顶级': ['AMD', 'ASML', 'COHR', 'ANET', 'CRWV', 'OKLO', 'VRT'],
  '💪 人上人': ['INTC', 'MRVL', 'QCOM', 'AMAT', 'KLAC', 'LRCX'],
  '😐 NPC': ['ADI', 'TXN', 'MCHP', 'ON', 'STM'],
  '💩 拉完了': ['POET', 'AXTI', 'MXL'],
  '☠️ 答辩': ['DRAM'],
}
const SAMPLE_DIST = {
  '🔥 夯死了': 5, '👑 顶级': 12, '💪 人上人': 24,
  '😐 NPC': 24, '💩 拉完了': 15, '☠️ 答辩': 1,
}

export default function Preview() {
  return (
    <>
      <Hero
        title="组件预览之页"
        emphasis="预览"
        subtitle="DESIGN LANGUAGE QA · 报纸黑 + 奶油白 + 旧奖杯金"
      />

      <section className="py-10 border-b border-ink">
        <div className="kicker mb-4">— TIER BADGES —</div>
        <div className="flex flex-wrap gap-3 items-center">
          {Object.keys(SAMPLE_TIERS).map((t) => <TierBadge key={t} tier={t} />)}
        </div>
      </section>

      <section className="py-10 border-b border-ink">
        <div className="kicker mb-4">— PERSONA PILLS —</div>
        <div className="flex flex-wrap gap-3 items-center">
          <PersonaPill persona="稳健白马" />
          <PersonaPill persona="妖股" />
          <PersonaPill persona="财报敏感型" />
          <PersonaPill persona="周期之神" />
        </div>
      </section>

      <section className="py-10 border-b border-ink">
        <div className="kicker mb-4">— STOCK CHIPS —</div>
        <div className="flex flex-wrap gap-2 items-center">
          {['NVDA', 'AVGO', 'TSM', 'AMD', 'AMAT', 'KLAC', 'ASML'].map((t) => (
            <StockChip key={t} ticker={t} />
          ))}
        </div>
      </section>

      <section className="py-10 border-b border-ink">
        <div className="kicker mb-4">— TIER BAR —</div>
        <TierBar distribution={SAMPLE_DIST} />
      </section>

      <section className="py-10 border-b border-ink">
        <div className="kicker mb-4">— AWARD CARDS —</div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 border-l border-t border-ink">
          <AwardCard award={SAMPLE_AWARD} />
          <AwardCard award={SAMPLE_BAD} />
          <AwardCard award={{ ...SAMPLE_AWARD, code: 'comeback', name: '🪄 绝地翻身奖', description: '从坑里爬出来' }} />
        </div>
      </section>

      <section className="py-10">
        <div className="kicker mb-4">— TIER TABLE —</div>
        <TierTable members={SAMPLE_TIERS} />
      </section>
    </>
  )
}
