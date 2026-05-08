import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/format'

const LINKS = [
  { to: '/', label: '今日', end: true },
  { to: '/hall', label: '名人堂' },
  { to: '/race', label: 'Race' },
  { to: '/portfolio', label: '持仓' },
]

export function Nav() {
  return (
    <header className="sticky top-0 z-40 h-16 bg-surface border-b border-border backdrop-blur">
      <div className="max-w-page mx-auto h-full px-6 flex items-center justify-between">
        <NavLink to="/" className="flex items-center gap-2 zh font-bold text-text">
          <span className="text-xl">🎖️</span>
          <span>股票颁奖典礼</span>
        </NavLink>
        <nav className="flex items-center gap-6">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                cn(
                  'zh text-sm py-1 border-b-2 transition-colors',
                  isActive
                    ? 'text-gold border-gold'
                    : 'text-muted border-transparent hover:text-text',
                )
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  )
}
