"""Awards routes."""
from __future__ import annotations

import json

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from api.awards_meta import meta_for
from api.deps import get_db
from api.models import AwardGroup, AwardWinner, LeaderboardEntry, TodayAwards

router = APIRouter(prefix="/awards", tags=["awards"])


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


def _bundle_period_awards(con: duckdb.DuckDBPyConnection, period: str, key: str) -> list[AwardGroup]:
    rows = con.execute(
        """
        SELECT award_code, rank, ticker, metric, meta
        FROM awards
        WHERE period = ? AND period_key = ?
        ORDER BY award_code, rank
        """,
        [period, key],
    ).fetchall()
    by_code: dict[str, list[AwardWinner]] = {}
    for code, rank, ticker, metric, meta in rows:
        by_code.setdefault(code, []).append(
            AwardWinner(rank=rank, ticker=ticker, metric=metric or 0.0, meta=_meta_to_dict(meta))
        )
    out: list[AwardGroup] = []
    for code, winners in by_code.items():
        m = meta_for(code)
        out.append(AwardGroup(code=code, name=m["name"], description=m["desc"], winners=winners))
    return out


@router.get("/today", response_model=TodayAwards)
def today(con: duckdb.DuckDBPyConnection = Depends(get_db)) -> TodayAwards:
    row = con.execute("SELECT MAX(period_key) FROM awards WHERE period = 'D'").fetchone()
    if not row or not row[0]:
        raise HTTPException(404, "no daily awards")
    key = row[0]
    groups = _bundle_period_awards(con, "D", key)
    tier_rows = con.execute(
        "SELECT tier, COUNT(*) FROM tiers WHERE date = ? GROUP BY tier", [key]
    ).fetchall()
    tier_dist = {t: int(c) for t, c in tier_rows}
    return TodayAwards(date=key, awards=groups, tier_distribution=tier_dist)


@router.get("/period/{period}/{key}", response_model=TodayAwards)
def period_awards(
    period: str, key: str, con: duckdb.DuckDBPyConnection = Depends(get_db)
) -> TodayAwards:
    if period not in {"D", "W", "M", "Q", "H", "Y", "E"}:
        raise HTTPException(400, "invalid period")
    groups = _bundle_period_awards(con, period, key)
    if not groups:
        raise HTTPException(404, f"no awards for {period}/{key}")
    tier_dist: dict[str, int] = {}
    if period == "D":
        tier_rows = con.execute(
            "SELECT tier, COUNT(*) FROM tiers WHERE date = ? GROUP BY tier", [key]
        ).fetchall()
        tier_dist = {t: int(c) for t, c in tier_rows}
    return TodayAwards(date=key, awards=groups, tier_distribution=tier_dist)


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(
    period: str = Query("D"),
    limit: int = Query(20, ge=1, le=200),
    con: duckdb.DuckDBPyConnection = Depends(get_db),
) -> list[LeaderboardEntry]:
    if period not in {"D", "W", "M", "Q", "H", "Y", "E"}:
        raise HTTPException(400, "invalid period")
    rows = con.execute(
        """
        SELECT a.ticker,
               SUM(CASE WHEN a.rank = 1 THEN 1 ELSE 0 END) AS gold,
               SUM(CASE WHEN a.rank = 2 THEN 1 ELSE 0 END) AS silver,
               SUM(CASE WHEN a.rank = 3 THEN 1 ELSE 0 END) AS bronze,
               COUNT(*) AS total,
               (SELECT persona FROM personas p WHERE p.ticker = a.ticker) AS persona
        FROM awards a
        WHERE a.period = ?
        GROUP BY a.ticker
        ORDER BY gold DESC, total DESC, a.ticker
        LIMIT ?
        """,
        [period, limit],
    ).fetchall()
    return [
        LeaderboardEntry(
            ticker=r[0], gold=int(r[1]), silver=int(r[2]), bronze=int(r[3]),
            total=int(r[4]), persona=r[5],
        )
        for r in rows
    ]
