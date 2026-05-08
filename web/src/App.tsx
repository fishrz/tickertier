import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import Today from '@/pages/Today'
import Preview from '@/pages/Preview'
import { StockDetail, HallOfFame, Race, Portfolio } from '@/pages/Stubs'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Today />} />
          <Route path="stock/:ticker" element={<StockDetail />} />
          <Route path="hall" element={<HallOfFame />} />
          <Route path="race" element={<Race />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="preview" element={<Preview />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
