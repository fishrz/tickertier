"""Awards routes."""
from __future__ import annotations

import json

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from api.awards_meta import AWARD_META, meta_for
from api.deps import get_db
from api.models import AwardGroup, AwardTopEntry, AwardWinner, LeaderboardEntry, TodayAwards

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


@router.get("/today/tiers")
def today_tiers(con: duckdb.DuckDBPyConnection = Depends(get_db)) -> dict:
    """Return today's tier members grouped by tier name."""
    row = con.execute("SELECT MAX(date) FROM tiers").fetchone()
    if not row or not row[0]:
        raise HTTPException(404, "no tiers")
    key = row[0]
    rows = con.execute(
        "SELECT tier, ticker FROM tiers WHERE date = ? AND ticker != 'QQQ' ORDER BY tier, ticker",
        [key],
    ).fetchall()
    members: dict[str, list[str]] = {}
    for tier, tk in rows:
        members.setdefault(tier, []).append(tk)
    return {"date": str(key), "members": members}


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
    valid = {"D", "W", "M", "Q", "H", "Y", "E", "ALL"}
    if period not in valid:
        raise HTTPException(400, f"invalid period, must be one of {sorted(valid)}")
    where = "1=1" if period == "ALL" else "a.period = ?"
    params: list = [] if period == "ALL" else [period]
    rows = con.execute(
        f"""
        SELECT a.ticker,
               SUM(CASE WHEN a.rank = 1 THEN 1 ELSE 0 END) AS gold,
               SUM(CASE WHEN a.rank = 2 THEN 1 ELSE 0 END) AS silver,
               SUM(CASE WHEN a.rank = 3 THEN 1 ELSE 0 END) AS bronze,
               COUNT(*) AS total,
               (SELECT persona FROM personas p WHERE p.ticker = a.ticker) AS persona
        FROM awards a
        WHERE {where}
        GROUP BY a.ticker
        ORDER BY gold DESC, total DESC, a.ticker
        LIMIT ?
        """,
        params + [limit],
    ).fetchall()
    return [
        LeaderboardEntry(
            ticker=r[0], gold=int(r[1]), silver=int(r[2]), bronze=int(r[3]),
            total=int(r[4]), persona=r[5],
        )
        for r in rows
    ]


@router.get("/by-code/{code}/top", response_model=list[AwardTopEntry])
def by_code_top(
    code: str,
    n: int = Query(3, ge=1, le=50),
    con: duckdb.DuckDBPyConnection = Depends(get_db),
) -> list[AwardTopEntry]:
    """Return top N historical winners for a given award code, ranked by gold then total wins."""
    rows = con.execute(
        """
        SELECT a.ticker,
               COUNT(*) AS total_wins,
               SUM(CASE WHEN a.rank = 1 THEN 1 ELSE 0 END) AS gold,
               SUM(CASE WHEN a.rank = 2 THEN 1 ELSE 0 END) AS silver,
               SUM(CASE WHEN a.rank = 3 THEN 1 ELSE 0 END) AS bronze
        FROM awards a
        WHERE a.award_code = ?
        GROUP BY a.ticker
        ORDER BY gold DESC, total_wins DESC, a.ticker
        LIMIT ?
        """,
        [code, n],
    ).fetchall()
    if not rows:
        raise HTTPException(404, f"no results for award code '{code}'")
    return [
        AwardTopEntry(
            ticker=r[0], total_wins=int(r[1]),
            gold=int(r[2]), silver=int(r[3]), bronze=int(r[4]),
        )
        for r in rows
    ]



@router.get("/meta/{code}")
def award_meta(
    code: str,
    con: "duckdb.DuckDBPyConnection" = Depends(get_db),
) -> dict:
    """Full award metadata for the info modal: name, joke, criterion, formula,
    plus historical top holders and total times awarded."""
    if code not in AWARD_META:
        raise HTTPException(404, f"unknown award code: {code}")
    meta = dict(AWARD_META[code])
    meta["code"] = code

    # Top historical winners (rank=1) for this award
    top = con.execute(
        """
        SELECT ticker, COUNT(*) AS wins
        FROM awards
        WHERE award_code = ? AND rank = 1
        GROUP BY ticker
        ORDER BY wins DESC, ticker ASC
        LIMIT 8
        """,
        [code],
    ).fetchall()

    total = con.execute(
        "SELECT COUNT(*) FROM awards WHERE award_code = ?",
        [code],
    ).fetchone()[0]

    last = con.execute(
        """
        SELECT period_key, ticker, metric
        FROM awards
        WHERE award_code = ? AND rank = 1
        ORDER BY period_key DESC
        LIMIT 1
        """,
        [code],
    ).fetchone()

    return {
        "meta": meta,
        "top_holders": [{"ticker": t, "wins": int(w)} for t, w in top],
        "total_awarded": int(total),
        "last_winner": (
            {"period_key": last[0], "ticker": last[1], "value": float(last[2]) if last[2] is not None else None}
            if last else None
        ),
    }


@router.get("/meta")
def award_meta_all() -> dict:
    """All award metadata in one call — used by the glossary page."""
    return {code: dict(meta) | {"code": code} for code, meta in AWARD_META.items()}
