import { Link } from 'react-router-dom'
import type { TierName } from '@/types'

const ORDER: TierName[] = [
  '🔥 夯死了', '👑 顶级', '💪 人上人', '😐 NPC', '💩 拉完了', '☠️ 答辩',
]

const STRIPE: Record<TierName, string> = {
  '🔥 夯死了': 'var(--tier-fire)',
  '👑 顶级': 'var(--tier-crown)',
  '💪 人上人': 'var(--tier-jade)',
  '😐 NPC': 'var(--tier-npc)',
  '💩 拉完了': 'var(--tier-poop)',
  '☠️ 答辩': 'var(--tier-skull)',
}

// Special chip styling per tier (only 夯死了 reverses to ink+gold; 答辩 reverses to red+paper)
function chipClass(tier: TierName) {
  if (tier === '🔥 夯死了') return 'bg-ink text-gold border-ink hover:bg-gold hover:text-ink'
  if (tier === '☠️ 答辩') return 'bg-neg text-paper border-neg hover:bg-ink hover:border-ink'
  return 'bg-paper text-ink border-ink hover:bg-ink hover:text-paper'
}

interface Props {
  members: Record<string, string[]>  // tier -> tickers[]
}

export function TierTable({ members }: Props) {
  return (
    <table className="w-full border-collapse border-t-[2px] border-b-[2px] border-ink">
      <tbody>
        {ORDER.map((tier) => {
          const list = members[tier] || []
          return (
            <tr key={tier} className="border-b border-ink last:border-b-0">
              <td
                className="w-[200px] py-6 pl-5 pr-6 align-top border-r border-ink relative"
                style={{
                  backgroundImage: `linear-gradient(${STRIPE[tier]}, ${STRIPE[tier]})`,
                  backgroundSize: '4px calc(100% - 48px)',
                  backgroundPosition: 'left 24px',
                  backgroundRepeat: 'no-repeat',
                }}
              >
                <div className="font-serif font-black text-[22px] leading-[1.1] mb-1.5">
                  {tier}
                </div>
                <div className="font-mono text-[11px] uppercase tracking-[0.15em] text-mute">
                  {list.length} 支
                </div>
              </td>
              <td className="p-6 leading-[2]">
                {list.length === 0 ? (
                  <span className="text-mute font-mono text-[12px]">— 今日无 —</span>
                ) : (
                  list.map((tk) => (
                    <Link
                      key={tk}
                      to={`/stock/${tk}`}
                      className={`inline-block font-mono font-medium text-[13px] px-2.5 py-1 mr-1 my-0.5 border transition-colors ${chipClass(tier)}`}
                    >
                      {tk}
                    </Link>
                  ))
                )}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
