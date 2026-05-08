"""Stocks routes."""
from __future__ import annotations

import json

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_db
from api.models import StockProfile
from data.db import universe

router = APIRouter(prefix="/stocks", tags=["stocks"])


def _universe_lookup() -> dict[str, dict]:
    return {u["ticker"]: u for u in universe()}


@router.get("/{ticker}", response_model=StockProfile)
def stock_profile(
    ticker: str, con: duckdb.DuckDBPyConnection = Depends(get_db)
) -> StockProfile:
    ticker = ticker.upper()
    uni = _universe_lookup()
    if ticker not in uni:
        raise HTTPException(404, f"unknown ticker {ticker}")
    info = uni[ticker]

    # persona + tier_dist
    p_row = con.execute(
        "SELECT persona, tier_dist FROM personas WHERE ticker = ?", [ticker]
    ).fetchone()
    persona = p_row[0] if p_row else None
    if p_row and p_row[1]:
        try:
            tier_dist = json.loads(p_row[1]) if isinstance(p_row[1], str) else dict(p_row[1])
        except Exception:
            tier_dist = {}
    else:
        # fallback compute from tiers
        rows = con.execute(
            "SELECT tier, COUNT(*) FROM tiers WHERE ticker = ? GROUP BY tier", [ticker]
        ).fetchall()
        total = sum(c for _, c in rows) or 1
        tier_dist = {t: c / total for t, c in rows}

    # medal counts
    med_rows = con.execute(
        "SELECT award_code, COUNT(*) FROM awards WHERE ticker = ? GROUP BY award_code", [ticker]
    ).fetchall()
    medal_count = {code: int(c) for code, c in med_rows}

    # last close + pct change
    last = con.execute(
        """
        SELECT p.date, p.close, dm.pct_change
        FROM prices p
        LEFT JOIN daily_metrics dm ON dm.ticker = p.ticker AND dm.date = p.date
        WHERE p.ticker = ?
        ORDER BY p.date DESC
        LIMIT 1
        """,
        [ticker],
    ).fetchone()
    last_close = float(last[1]) if last else 0.0
    last_pct = float(last[2]) if last and last[2] is not None else 0.0

    # recent 30d
    recent_rows = con.execute(
        """
        SELECT p.date, p.close, dm.pct_change, t.tier
        FROM prices p
        LEFT JOIN daily_metrics dm ON dm.ticker = p.ticker AND dm.date = p.date
        LEFT JOIN tiers t ON t.ticker = p.ticker AND t.date = p.date
        WHERE p.ticker = ?
        ORDER BY p.date DESC
        LIMIT 30
        """,
        [ticker],
    ).fetchall()
    recent_30d = [
        {
            "date": str(r[0]),
            "close": float(r[1]),
            "pct_change": float(r[2]) if r[2] is not None else 0.0,
            "tier": r[3],
        }
        for r in reversed(recent_rows)
    ]

    return StockProfile(
        ticker=ticker,
        name=info.get("name", ticker),
        theme=info.get("theme", ""),
        persona=persona,
        medal_count=medal_count,
        tier_distribution=tier_dist,
        last_close=last_close,
        last_pct_change=last_pct,
        recent_30d=recent_30d,
    )


@router.get("/{ticker}/medals")
def stock_medals(
    ticker: str,
    period: str = Query("Y"),
    con: duckdb.DuckDBPyConnection = Depends(get_db),
) -> dict:
    ticker = ticker.upper()
    rows = con.execute(
        """
        SELECT award_code, rank, period_key, metric, meta
        FROM awards
        WHERE ticker = ? AND period = ?
        ORDER BY period_key DESC, award_code, rank
        """,
        [ticker, period],
    ).fetchall()
    by_code: dict[str, list[dict]] = {}
    for code, rank, key, metric, meta in rows:
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        by_code.setdefault(code, []).append(
            {"rank": rank, "period_key": key, "metric": metric, "meta": meta or {}}
        )
    return {"ticker": ticker, "period": period, "medals": by_code}
