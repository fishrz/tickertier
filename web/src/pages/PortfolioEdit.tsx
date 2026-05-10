import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

interface Position {
  ticker: string
  shares: string
  avg_cost: string
}

const STORAGE_KEY = 'tickertier_portfolio'

function loadPositions(): Position[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) {
      return parsed.map((p: { ticker?: string; shares?: number; avg_cost?: number }) => ({
        ticker: p.ticker ?? '',
        shares: p.shares != null ? String(p.shares) : '',
        avg_cost: p.avg_cost != null ? String(p.avg_cost) : '',
      }))
    }
    return []
  } catch {
    return []
  }
}

function savePositions(positions: Position[]) {
  const cleaned = positions
    .filter((p) => p.ticker.trim() !== '')
    .map((p) => ({
      ticker: p.ticker.trim().toUpperCase(),
      shares: parseFloat(p.shares) || 0,
      avg_cost: parseFloat(p.avg_cost) || 0,
    }))
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cleaned))
}

export default function PortfolioEdit() {
  const [positions, setPositions] = useState<Position[]>([])
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setPositions(loadPositions())
  }, [])

  const update = (index: number, field: keyof Position, value: string) => {
    setPositions((prev) =>
      prev.map((p, i) => (i === index ? { ...p, [field]: value } : p)),
    )
    setSaved(false)
  }

  const addRow = () => {
    setPositions((prev) => [...prev, { ticker: '', shares: '', avg_cost: '' }])
    setSaved(false)
  }

  const deleteRow = (index: number) => {
    setPositions((prev) => prev.filter((_, i) => i !== index))
    setSaved(false)
  }

  const handleSave = () => {
    savePositions(positions)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <>
      {/* Header */}
      <section className="pt-10 pb-6">
        <div className="kicker mb-2">— EDIT —</div>
        <h1 className="font-serif font-black text-[48px] leading-none tracking-[-0.03em] mb-2">
          编辑持仓
        </h1>
        <p className="text-sm text-mute mb-2 max-w-[600px] leading-relaxed">
          填写你的持仓信息。Ticker 会自动转大写，空行在保存时会被跳过。
        </p>
        <p className="text-[11px] text-mute italic border border-dashed border-mute inline-block px-3 py-1.5 bg-paper-2">
          持仓数据保存在浏览器本地。清除浏览器数据会丢失。
        </p>
      </section>

      {/* Table */}
      <section className="pb-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b-[2px] border-ink">
                <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute">
                  Ticker
                </th>
                <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute text-right">
                  Shares
                </th>
                <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.15em] text-mute text-right">
                  Avg Cost
                </th>
                <th className="py-3 w-12"></th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos, i) => (
                <tr
                  key={i}
                  className="border-b border-paper-2 hover:bg-paper-2 transition-colors"
                >
                  <td className="py-2 pr-4">
                    <input
                      type="text"
                      value={pos.ticker}
                      onChange={(e) => update(i, 'ticker', e.target.value)}
                      placeholder="AAPL"
                      className="w-full bg-transparent border border-ink/30 focus:border-ink px-2 py-1.5 font-mono font-bold text-[13px] uppercase outline-none transition-colors"
                    />
                  </td>
                  <td className="py-2 pr-4">
                    <input
                      type="number"
                      value={pos.shares}
                      onChange={(e) => update(i, 'shares', e.target.value)}
                      placeholder="100"
                      className="w-full bg-transparent border border-ink/30 focus:border-ink px-2 py-1.5 font-mono tabular-nums text-[13px] text-right outline-none transition-colors"
                    />
                  </td>
                  <td className="py-2 pr-4">
                    <input
                      type="number"
                      step="0.01"
                      value={pos.avg_cost}
                      onChange={(e) => update(i, 'avg_cost', e.target.value)}
                      placeholder="150.00"
                      className="w-full bg-transparent border border-ink/30 focus:border-ink px-2 py-1.5 font-mono tabular-nums text-[13px] text-right outline-none transition-colors"
                    />
                  </td>
                  <td className="py-2 pl-2">
                    <button
                      onClick={() => deleteRow(i)}
                      className="font-mono text-[11px] text-mute hover:text-neg transition-colors cursor-pointer"
                      title="删除此行"
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
              {positions.length === 0 && (
                <tr>
                  <td
                    colSpan={4}
                    className="py-8 text-center text-mute text-sm italic"
                  >
                    暂无持仓，点击下方添加。
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Actions */}
      <section className="pb-12 flex items-center gap-4 flex-wrap">
        <button
          onClick={addRow}
          className="font-mono text-[12px] uppercase tracking-[0.12em] px-4 py-2 border border-ink hover:bg-ink hover:text-paper transition-colors cursor-pointer"
        >
          + 添加一行
        </button>
        <button
          onClick={handleSave}
          className="font-mono text-[12px] uppercase tracking-[0.12em] px-5 py-2 bg-ink text-paper hover:bg-gold hover:text-ink transition-colors cursor-pointer font-bold"
        >
          {saved ? '✓ 已保存' : '保存'}
        </button>
        <Link
          to="/portfolio"
          className="font-mono text-[12px] uppercase tracking-[0.12em] text-mute hover:text-gold transition-colors"
        >
          ← 返回持仓
        </Link>
      </section>
    </>
  )
}
