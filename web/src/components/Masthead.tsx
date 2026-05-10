import { Link, NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getStats, getHealth } from '@/lib/api'

const NAV = [
  { to: '/', label: '今日颁奖' },
  { to: '/hall', label: '名人堂' },
  { to: '/race', label: '排名变迁' },
  { to: '/portfolio', label: '我的持仓' },
]

export function Masthead() {
  const today = new Date().toISOString().slice(0, 10)
  const statsQ = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    staleTime: 5 * 60 * 1000,
  })
  const s = statsQ.data

  const healthQ = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 30 * 1000,  // 30s heartbeat
    retry: 0,
  })
  const isLive = healthQ.isSuccess && healthQ.data?.status === 'ok'

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
        <div className="font-mono text-[11px] uppercase tracking-[0.15em] text-mute flex gap-x-6 gap-y-1 flex-wrap">
          <span>VOL. <b className="text-ink font-medium">I</b></span>
          <span title="自选 + 持仓股票池总数">
            STOCKS <b className="text-ink font-medium">{s ? s.universe : '—'}</b>
          </span>
          <span><b className="text-ink font-medium">{today}</b></span>
          <span
            className="inline-flex items-center gap-1.5"
            title={isLive ? '后端在线' : '后端离线 / 连接失败'}
          >
            <span
              aria-hidden
              className={
                'inline-block w-[7px] h-[7px] rounded-full ' +
                (isLive
                  ? 'bg-[#16a34a] shadow-[0_0_6px_rgba(22,163,74,0.6)] animate-pulse'
                  : 'bg-[#9ca3af]')
              }
            />
            <b className={isLive ? 'text-ink font-medium' : 'text-mute font-medium'}>
              {isLive ? 'LIVE' : 'OFFLINE'}
            </b>
          </span>
        </div>
      </div>
    </header>
  )
}
