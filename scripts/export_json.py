"""Export static JSON snapshots from awards.duckdb for the frontend.

Reads from awards.duckdb (read_only=True) and writes 6 JSON files to
web/public/data/ for the Vite/React static frontend.

Run: python scripts/export_json.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, date
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "awards.duckdb"
UNIVERSE_PATH = ROOT / "data" / "universe.json"
OUT_DIR = ROOT / "web" / "public" / "data"

# ── award metadata (inline to avoid import-path headaches) ─────────────
sys.path.insert(0, str(ROOT))
from api.awards_meta import meta_for  # noqa: E402

# ── helpers ────────────────────────────────────────────────────────────

def _meta_to_dict(raw) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}


def _jwrite(name: str, obj: object) -> Path:
    """Write *obj* as pretty JSON to OUT_DIR/<name>. Return the path."""
    p = OUT_DIR / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n")
    size_kb = p.stat().st_size / 1024
    print(f"  {name:15s}  {size_kb:7.1f} KB")
    return p


def export_snapshots(con, out_dir: Path = OUT_DIR, universe_path: Path = UNIVERSE_PATH) -> list[Path]:
    """Export static JSON snapshots from an open DuckDB connection."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def jwrite(name: str, obj: object) -> Path:
        p = out_dir / name
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n")
        size_kb = p.stat().st_size / 1024
        print(f"  {name:15s}  {size_kb:7.1f} KB")
        written.append(p)
        return p

    uni = json.loads(universe_path.read_text())
    uni_map = {u["ticker"]: u for u in uni}

    # ── 1. today.json ──────────────────────────────────────────────
    print("[today.json]")
    row = con.execute("SELECT MAX(period_key) FROM awards WHERE period = 'D'").fetchone()
    if not row or not row[0]:
        print("  WARNING: no daily awards found; writing empty today.json")
        today_key = str(date.today())
        today_awards = []
        tier_dist = {}
    else:
        today_key = str(row[0])
        rows = con.execute(
            """
            SELECT award_code, rank, ticker, metric, meta
            FROM awards
            WHERE period = 'D' AND period_key = ?
            ORDER BY award_code, rank
            """,
            [today_key],
        ).fetchall()
        by_code: dict[str, list[dict]] = {}
        for code, rank, ticker, metric, meta in rows:
            by_code.setdefault(code, []).append({
                "rank": rank,
                "ticker": ticker,
                "metric": round(float(metric), 4) if metric is not None else 0.0,
                "meta": _meta_to_dict(meta),
            })
        today_awards = []
        for code, winners in by_code.items():
            m = meta_for(code)
            today_awards.append({
                "code": code,
                "name": m["name"],
                "description": m["desc"],
                "winners": winners,
            })
        tier_rows = con.execute(
            "SELECT tier, COUNT(*) FROM tiers WHERE date = ? GROUP BY tier",
            [today_key],
        ).fetchall()
        tier_dist = {t: int(c) for t, c in tier_rows}

    jwrite("today.json", {
        "date": today_key,
        "awards": today_awards,
        "tier_distribution": tier_dist,
    })

    # ── 2. tiers.json ─────────────────────────────────────────────
    print("[tiers.json]")
    t_row = con.execute("SELECT MAX(date) FROM tiers").fetchone()
    if not t_row or not t_row[0]:
        print("  WARNING: no tiers found; writing empty tiers")
        t_key = None
        tiers_rows = []
    else:
        t_key = t_row[0]
        tiers_rows = con.execute(
            "SELECT ticker, tier, score, rank_pct FROM tiers WHERE date = ? ORDER BY tier, ticker",
            [t_key],
        ).fetchall()
    tiers_data = [
        {"ticker": tk, "tier": tier, "score": round(float(sc), 4), "rank_pct": round(float(rp), 4)}
        for tk, tier, sc, rp in tiers_rows
    ]
    # Static frontend contract: flat array of tier rows. web/src/lib/api.ts
    # groups this array client-side for the tier bar.
    jwrite("tiers.json", {"date": str(t_key) if t_key else None, "tiers": tiers_data})

    # ── 3. stocks.json ────────────────────────────────────────────
    print("[stocks.json]")
    pd_row = con.execute("SELECT MAX(date) FROM prices").fetchone()
    max_price_date = pd_row[0] if pd_row and pd_row[0] else None
    stock_rows = []
    if max_price_date:
        rows = con.execute(
            """
            SELECT p.ticker, p.close, dm.pct_change, dm.intraday_amp, dm.vol_ratio_20,
                   t.tier, pers.persona, pers.tier_dist
            FROM prices p
            LEFT JOIN daily_metrics dm ON dm.ticker = p.ticker AND dm.date = p.date
            LEFT JOIN tiers t ON t.ticker = p.ticker AND t.date = p.date
            LEFT JOIN personas pers ON pers.ticker = p.ticker
            WHERE p.date = ?
            ORDER BY p.ticker
            """,
            [max_price_date],
        ).fetchall()
        aw_rows = con.execute("SELECT ticker, COUNT(*) FROM awards GROUP BY ticker").fetchall()
        aw_by_ticker = {ticker: int(count) for ticker, count in aw_rows}
        # medal_history per ticker — AGGREGATED by award_code (NOT raw rows).
        # Each entry: {code, name, count, gold, silver, bronze, latest_period_key,
        #              latest_period, best_rank}. This is what the StockDetail
        # 获奖履历 grid renders — one card per award type.
        mh_rows = con.execute(
            """
            SELECT ticker, award_code,
                   COUNT(*) AS total,
                   SUM(CASE WHEN rank = 1 THEN 1 ELSE 0 END) AS gold,
                   SUM(CASE WHEN rank = 2 THEN 1 ELSE 0 END) AS silver,
                   SUM(CASE WHEN rank = 3 THEN 1 ELSE 0 END) AS bronze,
                   MIN(rank) AS best_rank,
                   MAX(period_key) AS latest_pk,
                   ANY_VALUE(period) AS any_period
            FROM awards
            GROUP BY ticker, award_code
            ORDER BY ticker, total DESC
            """
        ).fetchall()
        medal_hist_by_ticker: dict[str, list[dict]] = {}
        for mtk, mcode, mtotal, mgold, msilver, mbronze, mbest, mlatest, mperiod in mh_rows:
            try:
                m = meta_for(mcode)
                pretty_name = m.get("name") or mcode
            except Exception:
                pretty_name = mcode
            medal_hist_by_ticker.setdefault(mtk, []).append({
                "code": mcode,
                "name": pretty_name,
                "count": int(mtotal),
                "gold": int(mgold),
                "silver": int(msilver),
                "bronze": int(mbronze),
                "best_rank": int(mbest) if mbest is not None else None,
                "latest_period_key": str(mlatest) if mlatest else None,
                "period": mperiod,
            })

        # tier_distribution per ticker (last 90 days)
        td_rows = con.execute(
            """
            SELECT ticker, tier, COUNT(*) as cnt
            FROM tiers
            WHERE date >= (SELECT MAX(date) - INTERVAL 90 DAY FROM tiers)
            GROUP BY ticker, tier
            ORDER BY ticker
            """
        ).fetchall()
        tier_counts_by_ticker: dict[str, dict[str, int]] = {}
        for tdk, td_tier, td_cnt in td_rows:
            tier_counts_by_ticker.setdefault(tdk, {})[td_tier] = int(td_cnt)
        tier_dist_by_ticker: dict[str, dict[str, float]] = {}
        for tdk, counts in tier_counts_by_ticker.items():
            total = sum(counts.values())
            tier_dist_by_ticker[tdk] = {t: round(c / total, 4) for t, c in counts.items()} if total > 0 else {}

        # recent_30d per ticker — INCLUDES tier per day
        r30_rows = con.execute(
            """
            SELECT p.ticker, p.date, p.close, dm.pct_change, t.tier
            FROM prices p
            LEFT JOIN daily_metrics dm ON dm.ticker = p.ticker AND dm.date = p.date
            LEFT JOIN tiers t ON t.ticker = p.ticker AND t.date = p.date
            WHERE p.date >= (SELECT MAX(date) - INTERVAL 45 DAY FROM prices)
            ORDER BY p.ticker, p.date ASC
            """
        ).fetchall()
        recent_by_ticker: dict[str, list[dict]] = {}
        for rtk, rd, rc, rp, rtier in r30_rows:
            recent_by_ticker.setdefault(rtk, []).append({
                "date": str(rd),
                "close": round(float(rc), 2) if rc else None,
                "pct_change": round(float(rp), 4) if rp is not None else None,
                "tier": rtier,
            })
        # Trim to last 30 (we read up to 45 calendar days; ~30 trading days)
        for k in recent_by_ticker:
            recent_by_ticker[k] = recent_by_ticker[k][-30:]

        for tk, close, pct, amp, vr20, tier, persona, _tier_dist_raw in rows:
            info = uni_map.get(tk, {})
            stock_rows.append({
                "ticker": tk,
                "name": info.get("name", tk),
                "theme": info.get("theme"),
                "close": round(float(close), 2) if close else None,
                "pct_change": round(float(pct), 4) if pct is not None else None,
                "intraday_amp": round(float(amp), 4) if amp is not None else None,
                "vol_ratio_20": round(float(vr20), 4) if vr20 is not None else None,
                "tier": tier,
                "awards_count": aw_by_ticker.get(tk, 0),
                "persona": persona,
                "medal_history": medal_hist_by_ticker.get(tk, []),
                "tier_distribution": tier_dist_by_ticker.get(tk, {}),
                "recent_30d": recent_by_ticker.get(tk, []),
            })
    # Static frontend contract: compact list for homepage/portfolio lookup.
    # Detailed by-ticker payloads are intentionally omitted to keep the daily
    # snapshot small and match web/src/lib/api.ts.
    jwrite("stocks.json", stock_rows)

    # ── 4. race.json ──────────────────────────────────────────────
    print("[race.json]")
    BENCH = frozenset({"QQQ"})
    bench_sql = ",".join(f"'{t}'" for t in BENCH) or "''"
    # ── Multi-granularity race data ──
    def build_race_frames(granularity: str, trunc_expr: str) -> list[dict]:
        """Build race frames for a given granularity."""
        BENCH = frozenset({"QQQ"})
        bench_sql = ",".join(f"'{t}'" for t in BENCH) or "''"
        bounds = con.execute(f"SELECT MIN(date), MAX(date) FROM prices WHERE ticker NOT IN ({bench_sql})").fetchone()
        frames = []
        if not bounds or not bounds[0]:
            return frames
        db_min, db_max = bounds
        end = db_max
        # Lookback depends on granularity
        lookback = {"D": 90, "W": 365, "M": 365 * 3, "Q": 365 * 5, "Y": 365 * 10}
        start = max(db_min, end - timedelta(days=lookback.get(granularity, 365 * 3)))
        frame_dates_rows = con.execute(
            f"""
            SELECT MAX(date) FROM prices
            WHERE ticker NOT IN ({bench_sql}) AND date BETWEEN ? AND ?
            GROUP BY {trunc_expr}
            ORDER BY 1
            """,
            [start, end],
        ).fetchall()
        frame_dates = [r[0] for r in frame_dates_rows]
        if not frame_dates:
            return frames
        base = con.execute(
            f"""
            SELECT ticker, FIRST(close ORDER BY date) AS base
            FROM prices
            WHERE ticker NOT IN ({bench_sql}) AND date >= ?
            GROUP BY ticker
            """,
            [start],
        ).fetchall()
        bmap = {t: float(b) for t, b in base if b}
        ph = ",".join(["?"] * len(frame_dates))
        close_rows = con.execute(
            f"""
            SELECT ticker, date, close
            FROM prices
            WHERE ticker NOT IN ({bench_sql}) AND date IN ({ph})
            """,
            list(frame_dates),
        ).fetchall()
        by_date: dict = {}
        for tk, d, c in close_rows:
            if tk not in bmap:
                continue
            by_date.setdefault(d, []).append((tk, (float(c) - bmap[tk]) / bmap[tk] * 100.0))
        for d in frame_dates:
            entries = sorted(by_date.get(d, []), key=lambda x: x[1], reverse=True)[:20]
            frames.append({
                "date": str(d),
                "entries": [
                    {"ticker": tk, "value": round(v, 4), "rank": i + 1}
                    for i, (tk, v) in enumerate(entries)
                ],
            })
        return frames

    race_data = {
        "daily": {"period": "D", "frames": build_race_frames("D", "date")},
        "weekly": {"period": "W", "frames": build_race_frames("W", "date_trunc('week', date)")},
        "monthly": {"period": "M", "frames": build_race_frames("M", "date_trunc('month', date)")},
        "quarterly": {"period": "Q", "frames": build_race_frames("Q", "date_trunc('quarter', date)")},
        "yearly": {"period": "Y", "frames": build_race_frames("Y", "date_trunc('year', date)")},
    }
    jwrite("race.json", race_data)

    # ── 7. portfolio_positions.json ────────────────────────────────
    print("[portfolio_positions.json]")
    portfolio_src = ROOT / "data" / "portfolio.json"
    if portfolio_src.exists():
        portfolio_data = json.loads(portfolio_src.read_text())
        jwrite("portfolio_positions.json", portfolio_data)
    else:
        print("  WARNING: data/portfolio.json not found")

    # ── 5. hall.json ──────────────────────────────────────────────
    # Schema:
    #   {
    #     "all_time": [...],                       # legacy / fallback
    #     "by_period": {"2026-05": [...], ...},    # legacy month/quarter/year keys
    #     "windows": {                             # NEW: time-window × granularity matrix
    #       "7d":  {"ALL": [...], "D": [...], "W": [...], ...},
    #       "30d": {...}, "90d": ..., "1y": ..., "3y": ..., "all": ...
    #     },
    #     "by_award_code": {                       # NEW: top 5 per award code (各项之王)
    #       "daily_king": [{ticker, gold, silver, bronze, total, persona}, ...],
    #       ...
    #     }
    #   }
    print("[hall.json]")

    def _agg_query(where_sql: str, params: list) -> list[dict]:
        sql = f"""
            SELECT a.ticker,
                   SUM(CASE WHEN a.rank = 1 THEN 1 ELSE 0 END) AS gold,
                   SUM(CASE WHEN a.rank = 2 THEN 1 ELSE 0 END) AS silver,
                   SUM(CASE WHEN a.rank = 3 THEN 1 ELSE 0 END) AS bronze,
                   COUNT(*) AS total,
                   (SELECT persona FROM personas p WHERE p.ticker = a.ticker) AS persona
            FROM awards a
            {where_sql}
            GROUP BY a.ticker
            HAVING COUNT(*) > 0
            ORDER BY gold DESC, total DESC, a.ticker
        """
        return [
            {"ticker": r[0], "gold": int(r[1]), "silver": int(r[2]),
             "bronze": int(r[3]), "total": int(r[4]), "persona": r[5]}
            for r in con.execute(sql, params).fetchall()
        ]

    # all_time (legacy + fallback)
    hall_data = _agg_query("", [])

    # ── windows × granularity ──
    # Window → cutoff date for daily-period awards.
    # Non-daily periods (W/M/Q/Y/E/H) are matched by lexicographic period_key
    # comparison after we derive a sensible cutoff key for each granularity.
    today_dt = date.today()
    win_days = {"7d": 7, "30d": 30, "90d": 90, "180d": 180, "1y": 365, "3y": 365 * 3, "all": None}

    GRANULARITIES = ["ALL", "D", "W", "M", "Q", "Y", "E", "H"]

    def _window_cutoff(days: int | None) -> date | None:
        if days is None:
            return None
        return today_dt - timedelta(days=days)

    def _window_pk_lower_bound(period: str, days: int | None) -> str | None:
        """Return a lexicographic lower-bound period_key for a granularity."""
        if days is None:
            return None
        cutoff = today_dt - timedelta(days=days)
        if period == "D" or period == "E" or period == "H":
            return cutoff.isoformat()
        if period == "W":
            iso_year, iso_week, _ = cutoff.isocalendar()
            return f"{iso_year}-W{iso_week:02d}"
        if period == "M":
            return f"{cutoff.year}-{cutoff.month:02d}"
        if period == "Q":
            q = (cutoff.month - 1) // 3 + 1
            return f"{cutoff.year}-Q{q}"
        if period == "Y":
            return str(cutoff.year)
        return cutoff.isoformat()

    windows_data: dict[str, dict[str, list[dict]]] = {}
    for win_key, days in win_days.items():
        per_gran: dict[str, list[dict]] = {}
        for gran in GRANULARITIES:
            if gran == "ALL":
                if days is None:
                    per_gran[gran] = hall_data[:50]
                else:
                    # Mixed-period filter: each period uses its own pk lower bound.
                    where_clauses = []
                    params: list = []
                    for p in ["D", "W", "M", "Q", "Y", "E", "H"]:
                        lb = _window_pk_lower_bound(p, days)
                        if lb:
                            where_clauses.append(f"(a.period = '{p}' AND CAST(a.period_key AS VARCHAR) >= ?)")
                            params.append(lb)
                    where_sql = "WHERE " + " OR ".join(where_clauses) if where_clauses else ""
                    per_gran[gran] = _agg_query(where_sql, params)[:50]
            else:
                if days is None:
                    per_gran[gran] = _agg_query("WHERE a.period = ?", [gran])[:50]
                else:
                    lb = _window_pk_lower_bound(gran, days)
                    if lb is None:
                        per_gran[gran] = _agg_query("WHERE a.period = ?", [gran])[:50]
                    else:
                        per_gran[gran] = _agg_query(
                            "WHERE a.period = ? AND CAST(a.period_key AS VARCHAR) >= ?",
                            [gran, lb],
                        )[:50]
        windows_data[win_key] = per_gran

    # ── by_award_code (各项之王 top 5) ──
    award_codes = [r[0] for r in con.execute(
        "SELECT DISTINCT award_code FROM awards ORDER BY award_code"
    ).fetchall()]
    by_award_code: dict[str, list[dict]] = {}
    for code in award_codes:
        rows_top = con.execute(
            """
            SELECT a.ticker,
                   SUM(CASE WHEN a.rank = 1 THEN 1 ELSE 0 END) AS gold,
                   SUM(CASE WHEN a.rank = 2 THEN 1 ELSE 0 END) AS silver,
                   SUM(CASE WHEN a.rank = 3 THEN 1 ELSE 0 END) AS bronze,
                   COUNT(*) AS total,
                   (SELECT persona FROM personas p WHERE p.ticker = a.ticker) AS persona
            FROM awards a
            WHERE a.award_code = ?
            GROUP BY a.ticker
            HAVING COUNT(*) > 0
            ORDER BY gold DESC, total DESC, a.ticker
            LIMIT 5
            """,
            [code],
        ).fetchall()
        by_award_code[code] = [
            {"ticker": r[0], "gold": int(r[1]), "silver": int(r[2]),
             "bronze": int(r[3]), "total": int(r[4]), "persona": r[5]}
            for r in rows_top
        ]

    # ── legacy by_period (month/quarter/year keys, for backwards compat) ──
    period_keys: list[str] = []
    for i in range(6):
        m = today_dt.month - i
        y = today_dt.year
        while m <= 0:
            m += 12
            y -= 1
        period_keys.append(f"{y}-{m:02d}")
    for y in range(today_dt.year, today_dt.year - 1, -1):
        for q in range(4, 0, -1):
            period_keys.append(f"{y}-Q{q}")
    for y in range(today_dt.year, today_dt.year - 2, -1):
        period_keys.append(str(y))
    period_keys = list(dict.fromkeys(period_keys))

    hall_by_period: dict[str, list[dict]] = {}
    for pk in period_keys:
        if "-Q" in pk:
            year, qnum = pk.split("-Q")
            qstart = int(qnum) * 3 - 2
            qend = int(qnum) * 3
            p_rows = _agg_query(
                "WHERE a.period = 'D' AND a.period_key >= ? AND a.period_key <= ?",
                [f"{year}-{qstart:02d}-01", f"{year}-{qend:02d}-31"],
            )
        else:
            p_rows = _agg_query(
                "WHERE a.period = 'D' AND CAST(a.period_key AS VARCHAR) LIKE ?",
                [f"{pk}%"],
            )
        hall_by_period[pk] = [
            {k: v for k, v in r.items() if k != "persona"} for r in p_rows
        ]

    jwrite("hall.json", {
        "all_time": hall_data[:50],
        "by_period": hall_by_period,
        "windows": windows_data,
        "by_award_code": by_award_code,
    })

    # ── 6. meta.json ──────────────────────────────────────────────
    print("[meta.json]")
    aw_count_row = con.execute("SELECT COUNT(*) FROM awards").fetchone()
    aw_count = int(aw_count_row[0]) if aw_count_row else 0
    date_range = con.execute("SELECT MIN(period_key), MAX(period_key) FROM awards WHERE period = 'D'").fetchone()
    data_from = str(date_range[0]) if date_range and date_range[0] else None
    data_to = str(date_range[1]) if date_range and date_range[1] else None
    jwrite("meta.json", {
        "last_updated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "universe": len(uni),
        "awards": aw_count,
        "data_from": data_from,
        "data_to": data_to,
    })

    return written


# ── main ───────────────────────────────────────────────────────────────

def main() -> None:
    import duckdb

    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        written = export_snapshots(con)
    finally:
        con.close()

    total_bytes = sum(p.stat().st_size for p in written)
    total_kb = total_bytes / 1024
    print(f"\nTotal: {total_kb:.1f} KB across {len(written)} files")
    if total_kb > 500:
        print(f"WARNING: total size {total_kb:.1f} KB exceeds 500 KB target!")
    print("Done.")


if __name__ == "__main__":
    main()
