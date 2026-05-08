import { Outlet } from 'react-router-dom'
import { Nav } from './Nav'

export function Layout() {
  return (
    <div className="min-h-screen bg-bg text-text">
      <Nav />
      <main className="max-w-page mx-auto px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
