"""Race route — bar chart race over cumulative metric."""
from __future__ import annotations

from datetime import date as _date
from datetime import datetime, timedelta

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_db
from api.models import RaceFrame, RaceResponse
from data.awards.registry import BENCHMARK_TICKERS

router = APIRouter(tags=["race"])


def _parse_date(s: str | None) -> _date | None:
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()


def _pick_granularity(start: _date, end: _date, period: str | None) -> str:
    if period in {"D", "W", "M"}:
        return period
    days = (end - start).days
    if days <= 180:
        return "D"
    if days <= 730:
        return "W"
    return "M"


def _bench_filter() -> str:
    return ",".join(f"'{t}'" for t in BENCHMARK_TICKERS) or "''"


@router.get("/race", response_model=RaceResponse)
def race(
    metric: str = Query("cum_return"),
    period: str | None = Query(None),
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None),
    top_n: int = Query(20, ge=3, le=80),
    con: duckdb.DuckDBPyConnection = Depends(get_db),
) -> RaceResponse:
    if metric not in {"cum_return", "medals"}:
        raise HTTPException(400, "metric must be cum_return or medals")

    bench = _bench_filter()
    bounds = con.execute(f"SELECT MIN(date), MAX(date) FROM prices WHERE ticker NOT IN ({bench})").fetchone()
    if not bounds or not bounds[0]:
        return RaceResponse(metric=metric, period="D", frames=[])
    db_min, db_max = bounds
    start = _parse_date(from_) or db_min
    end = _parse_date(to) or db_max
    if start < db_min:
        start = db_min
    if end > db_max:
        end = db_max
    granularity = _pick_granularity(start, end, period)

    # Pick frame dates from prices (trading days only).
    if granularity == "D":
        frame_dates_rows = con.execute(
            f"SELECT DISTINCT date FROM prices WHERE ticker NOT IN ({bench}) "
            "AND date BETWEEN ? AND ? ORDER BY date",
            [start, end],
        ).fetchall()
    elif granularity == "W":
        frame_dates_rows = con.execute(
            f"""
            SELECT MAX(date) FROM prices WHERE ticker NOT IN ({bench})
            AND date BETWEEN ? AND ?
            GROUP BY date_trunc('week', date) ORDER BY 1
            """,
            [start, end],
        ).fetchall()
    else:  # M
        frame_dates_rows = con.execute(
            f"""
            SELECT MAX(date) FROM prices WHERE ticker NOT IN ({bench})
            AND date BETWEEN ? AND ?
            GROUP BY date_trunc('month', date) ORDER BY 1
            """,
            [start, end],
        ).fetchall()
    frame_dates = [r[0] for r in frame_dates_rows]
    if not frame_dates:
        return RaceResponse(metric=metric, period=granularity, frames=[])

    if metric == "cum_return":
        # baseline close per ticker at-or-after start
        base = con.execute(
            f"""
            SELECT ticker, FIRST(close ORDER BY date) AS base
            FROM prices
            WHERE ticker NOT IN ({bench}) AND date >= ?
            GROUP BY ticker
            """,
            [start],
        ).fetchall()
        base_map = {t: float(b) for t, b in base if b}
        # closes at frame dates
        frame_set = tuple(frame_dates)
        # batch-fetch all closes at frame dates
        rows = con.execute(
            f"""
            SELECT ticker, date, close
            FROM prices
            WHERE ticker NOT IN ({bench}) AND date IN ({",".join(["?"] * len(frame_set))})
            """,
            list(frame_set),
        ).fetchall()
        by_date: dict = {}
        for tk, d, c in rows:
            if tk not in base_map:
                continue
            by_date.setdefault(d, []).append((tk, (float(c) - base_map[tk]) / base_map[tk] * 100.0))
        frames: list[RaceFrame] = []
        for d in frame_dates:
            entries = sorted(by_date.get(d, []), key=lambda x: x[1], reverse=True)[:top_n]
            frames.append(
                RaceFrame(
                    date=str(d),
                    entries=[
                        {"ticker": tk, "value": round(v, 4), "rank": i + 1}
                        for i, (tk, v) in enumerate(entries)
                    ],
                )
            )
        return RaceResponse(metric=metric, period=granularity, frames=frames)

    # metric == "medals" — cumulative gold (rank=1 daily) up to frame date
    rows = con.execute(
        f"""
        SELECT period_key, ticker, COUNT(*) AS golds
        FROM awards
        WHERE period = 'D' AND rank = 1 AND ticker NOT IN ({bench})
        AND period_key BETWEEN ? AND ?
        GROUP BY period_key, ticker
        """,
        [str(start), str(end)],
    ).fetchall()
    # Build per-day gold counts dict
    daily: dict[str, dict[str, int]] = {}
    for k, tk, n in rows:
        daily.setdefault(k, {})[tk] = int(n)

    cum: dict[str, int] = {}
    frames: list[RaceFrame] = []
    sorted_keys = sorted(daily.keys())
    key_iter = iter(sorted_keys)
    next_key: str | None = next(key_iter, None)
    for fd in frame_dates:
        fd_str = str(fd)
        while next_key is not None and next_key <= fd_str:
            for tk, n in daily[next_key].items():
                cum[tk] = cum.get(tk, 0) + n
            next_key = next(key_iter, None)
        entries = sorted(cum.items(), key=lambda x: x[1], reverse=True)[:top_n]
        frames.append(
            RaceFrame(
                date=fd_str,
                entries=[
                    {"ticker": tk, "value": v, "rank": i + 1}
                    for i, (tk, v) in enumerate(entries)
                ],
            )
        )
    return RaceResponse(metric=metric, period=granularity, frames=frames)
