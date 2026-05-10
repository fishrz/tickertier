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
    jwrite("tiers.json", tiers_data)

    # ── 3. stocks.json ────────────────────────────────────────────
    print("[stocks.json]")
    pd_row = con.execute("SELECT MAX(date) FROM prices").fetchone()
    max_price_date = pd_row[0] if pd_row and pd_row[0] else None
    stock_rows = []
    stock_detail: dict[str, dict] = {}
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
        for tk, close, pct, amp, vr20, tier, persona, tier_dist_raw in rows:
            info = uni_map.get(tk, {})
            stock_rows.append({
                "ticker": tk,
                "name": info.get("name", tk),
                "close": round(float(close), 2) if close else None,
                "pct_change": round(float(pct), 4) if pct is not None else None,
                "intraday_amp": round(float(amp), 4) if amp is not None else None,
                "vol_ratio_20": round(float(vr20), 4) if vr20 is not None else None,
                "tier": tier,
                "awards_count": aw_by_ticker.get(tk, 0),
                "persona": persona,
            })
    # Static frontend contract: compact list for homepage/portfolio lookup.
    # Detailed by-ticker payloads are intentionally omitted to keep the daily
    # snapshot small and match web/src/lib/api.ts.
    jwrite("stocks.json", stock_rows)

    # ── 4. race.json ──────────────────────────────────────────────
    print("[race.json]")
    BENCH = frozenset({"QQQ"})
    bench_sql = ",".join(f"'{t}'" for t in BENCH) or "''"
    bounds = con.execute(f"SELECT MIN(date), MAX(date) FROM prices WHERE ticker NOT IN ({bench_sql})").fetchone()
    race_frames = []
    if bounds and bounds[0]:
        db_min, db_max = bounds
        end = db_max
        start = max(db_min, end - timedelta(days=365 * 3))
        frame_dates_rows = con.execute(
            f"""
            SELECT MAX(date) FROM prices
            WHERE ticker NOT IN ({bench_sql}) AND date BETWEEN ? AND ?
            GROUP BY date_trunc('month', date)
            ORDER BY 1
            """,
            [start, end],
        ).fetchall()
        frame_dates = [r[0] for r in frame_dates_rows]
        if frame_dates:
            base = con.execute(
                f"""
                SELECT ticker, FIRST(close ORDER BY date) AS base
                FROM prices
                WHERE ticker NOT IN ({bench_sql}) AND date >= ?
                GROUP BY ticker
                """,
                [start],
            ).fetchall()
            base_map = {t: float(b) for t, b in base if b}
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
                if tk not in base_map:
                    continue
                by_date.setdefault(d, []).append((tk, (float(c) - base_map[tk]) / base_map[tk] * 100.0))
            for d in frame_dates:
                entries = sorted(by_date.get(d, []), key=lambda x: x[1], reverse=True)[:20]
                race_frames.append({
                    "date": str(d),
                    "entries": [
                        {"ticker": tk, "value": round(v, 4), "rank": i + 1}
                        for i, (tk, v) in enumerate(entries)
                    ],
                })
    jwrite("race.json", {"metric": "cum_return", "period": "M", "frames": race_frames})

    # ── 5. hall.json ──────────────────────────────────────────────
    print("[hall.json]")
    hall_rows = con.execute(
        """
        SELECT a.ticker,
               SUM(CASE WHEN a.rank = 1 THEN 1 ELSE 0 END) AS gold,
               SUM(CASE WHEN a.rank = 2 THEN 1 ELSE 0 END) AS silver,
               SUM(CASE WHEN a.rank = 3 THEN 1 ELSE 0 END) AS bronze,
               COUNT(*) AS total,
               (SELECT persona FROM personas p WHERE p.ticker = a.ticker) AS persona
        FROM awards a
        GROUP BY a.ticker
        HAVING COUNT(*) > 0
        ORDER BY gold DESC, total DESC, a.ticker
        """,
    ).fetchall()
    hall_data = [
        {
            "ticker": r[0],
            "gold": int(r[1]),
            "silver": int(r[2]),
            "bronze": int(r[3]),
            "total": int(r[4]),
            "persona": r[5],
        }
        for r in hall_rows
    ]
    jwrite("hall.json", hall_data)

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
