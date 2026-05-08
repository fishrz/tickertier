import { Outlet } from 'react-router-dom'
import { Masthead } from './Masthead'

export function Layout() {
  return (
    <div className="min-h-screen bg-paper text-ink">
      <Masthead />
      <main className="max-w-page mx-auto px-[var(--page-pad-x)] pb-[120px]">
        <Outlet />
      </main>
      <footer className="max-w-page mx-auto px-[var(--page-pad-x)] mt-20">
        <div className="border-t-[4px] border-ink pt-6 pb-8 font-mono text-[11px] uppercase tracking-[0.15em] text-mute flex justify-between flex-wrap gap-4">
          <span>夯榜 · 个人娱乐用 · 不构成投资建议</span>
          <span>POWERED BY DUCKDB · YFINANCE · FINNHUB</span>
        </div>
      </footer>
    </div>
  )
}
