import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { Layout } from '@/components/Layout'
import Today from '@/pages/Today'

// Heavy routes are lazy-loaded so the Today landing chunk stays small.
// Each lazy() emits its own JS chunk, fetched only when the user navigates.
const StockDetail = lazy(() => import('@/pages/StockDetail'))
const HallOfFame = lazy(() => import('@/pages/HallOfFame'))
const Race = lazy(() => import('@/pages/Race'))
const Portfolio = lazy(() => import('@/pages/Portfolio'))
const PortfolioEdit = lazy(() => import('@/pages/PortfolioEdit'))
const Watchlist = lazy(() => import('@/pages/Watchlist'))
const Preview = lazy(() => import('@/pages/Preview'))
const Daily = lazy(() => import('@/pages/Daily'))

function PageFallback() {
  return (
    <div className="max-w-page mx-auto px-[var(--page-pad-x)] py-16">
      <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-mute">载入中…</div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Today />} />
          <Route
            path="stock/:ticker"
            element={
              <Suspense fallback={<PageFallback />}>
                <StockDetail />
              </Suspense>
            }
          />
          <Route
            path="hall"
            element={
              <Suspense fallback={<PageFallback />}>
                <HallOfFame />
              </Suspense>
            }
          />
          <Route
            path="race"
            element={
              <Suspense fallback={<PageFallback />}>
                <Race />
              </Suspense>
            }
          />
          <Route
            path="portfolio"
            element={
              <Suspense fallback={<PageFallback />}>
                <Portfolio />
              </Suspense>
            }
          />
          <Route
            path="preview"
            element={
              <Suspense fallback={<PageFallback />}>
                <Preview />
              </Suspense>
            }
          />
          <Route
            path="daily"
            element={
              <Suspense fallback={<PageFallback />}>
                <Daily />
              </Suspense>
            }
          />
          <Route
            path="portfolio/edit"
            element={
              <Suspense fallback={<PageFallback />}>
                <PortfolioEdit />
              </Suspense>
            }
          />
          <Route
            path="watch"
            element={
              <Suspense fallback={<PageFallback />}>
                <Watchlist />
              </Suspense>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
