import { Link, NavLink } from 'react-router-dom'

const NAV = [
  { to: '/', label: '今日颁奖' },
  { to: '/hall', label: '名人堂' },
  { to: '/race', label: '排名变迁' },
  { to: '/portfolio', label: '我的持仓' },
]

export function Masthead() {
  // Issue number = days since some epoch, just for flavor
  const issue = Math.floor((Date.now() - new Date('2023-05-08').getTime()) / 86400000)
  const today = new Date().toISOString().slice(0, 10)

  return (
    <header className="border-t-[4px] border-ink border-b border-ink">
      <div className="max-w-page mx-auto px-[var(--page-pad-x)] py-[18px] flex items-baseline justify-between gap-10 flex-wrap">
        <Link to="/" className="font-serif font-black text-[28px] leading-none tracking-[-0.02em]">
          夯榜<span className="text-gold">.</span>
          <span className="ml-2 font-mono text-[11px] font-normal tracking-[0.2em] text-mute">
            DAILY AWARDS
          </span>
        </Link>
        <nav className="flex gap-7 font-mono text-[11px] uppercase tracking-[0.18em]">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              className={({ isActive }) =>
                isActive
                  ? 'text-ink font-medium border-b-2 border-gold pb-[2px]'
                  : 'text-mute hover:text-ink'
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="font-mono text-[11px] uppercase tracking-[0.15em] text-mute flex gap-6">
          <span>VOL. <b className="text-ink font-medium">I</b></span>
          <span>ISSUE <b className="text-ink font-medium">{issue}</b></span>
          <span><b className="text-ink font-medium">{today}</b></span>
        </div>
      </div>
    </header>
  )
}
