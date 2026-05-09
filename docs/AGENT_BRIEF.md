# Stock Awards Platform — Agent Brief (shared context for all workers)

Read this once before doing your task. Updated 2026-05-08.

## What this app is
本地单用户美股「颁奖娱乐平台」。81 支 AI 基建股票，每天/周/月/季/年发奖、评 tier、做名人堂、bar chart race。后端已完成，前端剩余 4 个页面。

## Tech stack (DO NOT change)
- Backend: FastAPI on `127.0.0.1:8000` (already running, all routes implemented under `api/routes/`)
- Frontend: **Vite + React 18 + TypeScript + Tailwind + shadcn-style + TanStack Query + Recharts + Framer Motion** + React Router
- Data: DuckDB single file at `data/awards.duckdb` (already backfilled, 3y history, 81 tickers)
- Path: `/mnt/c/Users/YuRu/Documents/Projects/stock-awards`

## Visual language (HARD constraints — do not drift)
- **Theme**: 体育杂志 × 报纸编辑设计 × 棒球球员卡
- **Palette only**: 报纸黑 `#0E0E0E` / 奶油白 `#F4EFE6` / 旧奖杯金 `#B8893E` (+ 沉绿/沉红仅用于数字 ±)
- **Fonts only**: Noto Serif SC (大标题/headline), Noto Sans SC (body), JetBrains Mono (ticker/数字)
- **Forbidden**: 圆角 (`rounded-*` 全用 `rounded-none`), 阴影, 渐变, glow, neon, gradient text, blur, glassmorphism
- **Allowed**: 1px 黑色描边 (`border border-ink`), 4px 黑色粗线 (`border-t-4` 作为分隔), 高密度版式
- **Accent rule**: 一个页面只有 1 个主 accent (金)；tier 色只在 `<TierBadge>` 内允许
- 参考 `web/src/pages/Today.tsx`、`web/src/pages/Preview.tsx`、`web/mockup.html` 的语言

## Existing components you MUST reuse (don't rebuild)
`web/src/components/`:
- `Layout.tsx` — page frame (do not modify, just wrap)
- `Masthead.tsx` — top nav (导航条，含 Today/Stock/Hall/Race/Portfolio 链接，确认你的页面已被链接)
- `Hero.tsx` — page hero (accepts ReactNode title)
- `TierBadge.tsx` `TierBar.tsx` `TierTable.tsx`
- `AwardCard.tsx`
- `StockChip.tsx` — ticker chip (硬边)
- `PersonaPill.tsx`

`web/src/lib/`:
- `api.ts` — add new fetchers here, do NOT inline fetch in components
- `format.ts` — `formatPercent` `formatAmount` `formatMetric` `MEDALS` (① ② ③) `metricTone()`
- `tokens.css` 已定义 CSS vars, Tailwind 已映射

## Data sources (use existing API; if missing endpoint, add it to api/routes/)
Already implemented:
- `GET /awards/today` — 今日 daily + portfolio 奖项
- `GET /awards/today/tiers` — `{ as_of, members: { tier: [ticker...] } }`
- `GET /stocks/:ticker` — `{ ticker, persona, last_close, recent_30d (sparkline data), medal_count }`
- `GET /race?metric=cum_return|medal_count&period=Y|Q|M` — frames for bar chart race
- `GET /portfolio/today` — `{ positions, mv, today_pnl, pillar, traitor }`
- `GET /health`

If you need an endpoint that doesn't exist, ADD it to the matching `api/routes/*.py` file with a minimal handler + return Pydantic model + a pytest. Don't break existing tests (`pytest -q` must stay 62 passed, 2 skipped or better).

## Awards taxonomy (for reference)
17 awards total. Daily awards live in `data/awards/daily/`, periodic in `data/awards/periodic/`, portfolio in `data/awards/portfolio/`. Award metadata (display name, emoji, semantic tone) is in `api/awards_meta.py` — use it.

Tier order (high → low):
1. 🔥 夯爆了
2. 👑 顶级
3. 💪 人上人
4. 😐 NPC
5. 💩 拉胯
6. ☠️ 答辩

## Workflow rules
1. **Branch**: commit directly to `main` with a clear message (e.g. `feat(web): D4 stock detail page`).
2. **Build before commit**: `cd web && NODE_ENV=development npm run build` must pass with no TS errors.
3. **Backend tests**: if you touched `api/`, run `cd /mnt/c/Users/YuRu/Documents/Projects/stock-awards && pytest -q`.
4. **Visual smoke (HARD RULES — read carefully)**:
   - Use **`browser_cdp`** (stateless protocol calls). DO NOT use `browser_navigate` — it tries to auto-launch a fresh Chrome via the WSL bridge and will hang for 60s+ each call on this setup.
   - Pre-flight probe: `curl -s -m 3 http://127.0.0.1:9223/json/version` — must return Chrome version JSON. If it doesn't, abort and `kanban_block`; do NOT auto-launch.
   - Get a live page target: `curl -s http://127.0.0.1:9223/json | jq '.[] | select(.url|startswith("http://localhost:5173"))'`
   - Drive via `Page.navigate` + `Runtime.evaluate` over the page's `webSocketDebuggerUrl`. See `scripts/cdp_e2e_probe.py` in the `hermes-multi-profile-fanout` skill for a working example.
   - Save h1 + key DOM counts in your task summary.
5. **Vite WSL trap (verification preflight — MUST run before smoke)**:
   ```bash
   ps aux | grep -E "vite" | grep -v grep | awk '{print $2}' | xargs -r kill -9
   rm -rf web/node_modules/.vite web/dist
   sleep 2
   cd web && NODE_ENV=development nohup npm run dev > /tmp/vite.log 2>&1 &
   sleep 10  # wait for "ready in" + dependency optimization
   curl -s http://127.0.0.1:5173/ | grep -q '<div id="root">' || { echo "vite not ready"; exit 1; }
   ```
   If the page renders blank with `$RefreshReg$ is not defined` in console, the cache is stale — kill + clear + restart again. Verify with `curl -s http://127.0.0.1:5173/src/pages/<YourPage>.tsx | head` that you see CURRENT source.
6. **Routes**: register your new page in `web/src/App.tsx` and ensure `Masthead.tsx` link works.
7. **No SSR**: this is pure CSR Vite, no Next.js patterns.

## What "done" looks like for a page task
- Page renders with real data from API (no mock)
- Tailwind palette/font constraints honored (zero rounded corners, zero shadows)
- One main accent (gold) per page
- Loading + empty + error states handled (use a simple `<div>载入中…</div>` and a paper-style error block)
- Mobile breakpoint not required (desktop-first, 1280px+ design target)
- `npm run build` passes
- Browser CDP smoke shows expected DOM
- Commit on main with descriptive message
- `kanban_complete` summary includes: page route, commit hash, build output size, screenshot impressions

## Pitfalls already paid for (don't repeat)
- `QQQ` is benchmark — never let it appear in award contender lists. Already filtered in `data/awards/registry.py`.
- Don't run `npm install` without `NODE_ENV=development` (production install drops devDeps and breaks build). See skill `wsl-npm-node-env-trap`.
- DuckDB is single-writer. Don't run two pipeline scripts in parallel against `data/awards.duckdb`.
- Stale vite processes silently hold port 5173 — kill all before restart.
- File path is on `/mnt/c` (NTFS bridge), so prefer fewer file writes per build.
