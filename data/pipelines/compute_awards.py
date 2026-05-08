"""Orchestrator: compute all awards + tiers across a date range.

CLI:
    python -m data.pipelines.compute_awards --backfill 2023-05-05
    python -m data.pipelines.compute_awards --daily
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas_market_calendars as mcal

from data.awards._helpers import period_key_for
from data.awards.registry import awards_for_period, get_award
from data.awards.tier import compute_tiers
from data.db import get_conn, init_schema, universe
from data.pipelines.compute_metrics import compute_metrics
from data.pipelines.fetch_prices import run_incremental

log = logging.getLogger(__name__)

PORTFOLIO_PATH = Path(__file__).parent.parent / "portfolio.json"


def _trading_days(start: date, end: date) -> list[date]:
    cal = mcal.get_calendar("NYSE")
    sched = cal.schedule(start_date=start.isoformat(), end_date=end.isoformat())
    return [d.date() for d in sched.index]


def _write_award(con, code: str, period: str, period_key: str, results: list[tuple[str, float, dict]]) -> int:
    """Persist top 3 (or fewer) into awards. Idempotent per (code, period, key)."""
    con.execute(
        "DELETE FROM awards WHERE award_code = ? AND period = ? AND period_key = ?",
        [code, period, period_key],
    )
    rows = []
    for i, (ticker, score, meta) in enumerate(results[:3], start=1):
        rows.append((code, period, period_key, i, ticker, float(score), json.dumps(meta or {}, default=str)))
    if rows:
        con.executemany(
            "INSERT INTO awards (award_code, period, period_key, rank, ticker, metric, meta) VALUES (?,?,?,?,?,?,?)",
            rows,
        )
    return len(rows)


def _ensure_positions(con) -> None:
    """Load portfolio.json into positions table if positions is empty."""
    n = con.execute("SELECT count(*) FROM positions").fetchone()[0]
    if n > 0:
        return
    if not PORTFOLIO_PATH.exists():
        return
    pf = json.loads(PORTFOLIO_PATH.read_text())
    as_of = pf.get("as_of") or date.today().isoformat()
    rows = [
        (as_of, p["ticker"], float(p["shares"]), float(p.get("avg_cost", 0)))
        for p in pf.get("positions", [])
    ]
    if rows:
        con.executemany(
            "INSERT OR REPLACE INTO positions (date, ticker, shares, avg_cost) VALUES (?,?,?,?)",
            rows,
        )
        log.info("positions: loaded %d rows from portfolio.json", len(rows))


def run_daily_for(con, d: date) -> None:
    dk = d.isoformat()
    # 1. Daily awards
    for code in awards_for_period("D"):
        fn, _, _ = get_award(code)
        try:
            results = fn(con, dk, "D")
        except Exception as e:
            log.exception("award %s failed for %s: %s", code, dk, e)
            continue
        _write_award(con, code, "D", dk, results)
    # 2. Tier
    compute_tiers(con, dk)


def run_periodic_for(con, d: date, period: str) -> None:
    pk = period_key_for(d, period)
    for code in awards_for_period(period):
        fn, _, _ = get_award(code)
        try:
            results = fn(con, pk, period)
        except Exception as e:
            log.exception("award %s failed for %s/%s: %s", code, period, pk, e)
            continue
        _write_award(con, code, period, pk, results)


def run_earnings_awards(con) -> None:
    """Run earnings awards once per distinct report_date that has next_day_pct."""
    rows = con.execute(
        "SELECT DISTINCT report_date FROM earnings WHERE next_day_pct IS NOT NULL"
    ).fetchall()
    for (rd,) in rows:
        for code in ("earnings_god", "earnings_clown"):
            fn, _, _ = get_award(code)
            results = fn(con, rd.isoformat(), "E")
            _write_award(con, code, "E", rd.isoformat(), results)


def run_backfill(con, start: date, end: date | None = None) -> None:
    if end is None:
        end = date.today()
    init_schema(con)
    _ensure_positions(con)
    days = _trading_days(start, end)
    log.info("backfill: %d trading days from %s to %s", len(days), start, end)

    # Track period boundaries we've already computed
    seen_w, seen_m, seen_q, seen_h, seen_y = set(), set(), set(), set(), set()
    t0 = time.time()
    for i, d in enumerate(days):
        run_daily_for(con, d)
        # On the *last* trading day of each period (relative to days list), run periodic
        # We detect by comparing period_key with the next day's period_key
        is_last = (i == len(days) - 1) or (
            period_key_for(d, "W") != period_key_for(days[i + 1], "W")
        )
        if is_last:
            wk = period_key_for(d, "W")
            if wk not in seen_w:
                run_periodic_for(con, d, "W")
                seen_w.add(wk)
        is_last_m = (i == len(days) - 1) or (
            period_key_for(d, "M") != period_key_for(days[i + 1], "M")
        )
        if is_last_m:
            mk = period_key_for(d, "M")
            if mk not in seen_m:
                run_periodic_for(con, d, "M")
                seen_m.add(mk)
        is_last_q = (i == len(days) - 1) or (
            period_key_for(d, "Q") != period_key_for(days[i + 1], "Q")
        )
        if is_last_q:
            qk = period_key_for(d, "Q")
            if qk not in seen_q:
                run_periodic_for(con, d, "Q")
                seen_q.add(qk)
        is_last_h = (i == len(days) - 1) or (
            period_key_for(d, "H") != period_key_for(days[i + 1], "H")
        )
        if is_last_h:
            hk = period_key_for(d, "H")
            if hk not in seen_h:
                run_periodic_for(con, d, "H")
                seen_h.add(hk)
        is_last_y = (i == len(days) - 1) or (
            period_key_for(d, "Y") != period_key_for(days[i + 1], "Y")
        )
        if is_last_y:
            yk = period_key_for(d, "Y")
            if yk not in seen_y:
                run_periodic_for(con, d, "Y")
                seen_y.add(yk)

        if (i + 1) % 50 == 0:
            log.info("backfill: %d/%d days, elapsed %.1fs", i + 1, len(days), time.time() - t0)

    run_earnings_awards(con)
    log.info("backfill: done in %.1fs", time.time() - t0)


def run_daily(con) -> None:
    init_schema(con)
    _ensure_positions(con)
    run_incremental(con)
    compute_metrics(con)
    today = con.execute("SELECT max(date) FROM prices").fetchone()[0]
    if today is None:
        log.warning("no prices, skipping daily")
        return
    run_daily_for(con, today)
    # Run periodic for current period boundaries (idempotent)
    for period in ("W", "M", "Q", "H", "Y"):
        run_periodic_for(con, today, period)
    run_earnings_awards(con)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--backfill", metavar="START_DATE", help="YYYY-MM-DD")
    g.add_argument("--daily", action="store_true")
    p.add_argument("--end", metavar="END_DATE", help="YYYY-MM-DD (default: today)")
    args = p.parse_args()
    con = get_conn()
    try:
        if args.backfill:
            start = datetime.strptime(args.backfill, "%Y-%m-%d").date()
            end = (
                datetime.strptime(args.end, "%Y-%m-%d").date()
                if args.end
                else date.today()
            )
            run_backfill(con, start, end)
        else:
            run_daily(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
