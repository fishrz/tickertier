"""Stocks routes."""
from __future__ import annotations

import json

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_db
from api.models import StockProfile
from api.awards_meta import AWARD_META, meta_for
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

    # medal_history: per award_code, count + latest_date + best rank
    med_hist_rows = con.execute(
        """
        SELECT award_code, COUNT(*) as cnt,
               MAX(period_key) as latest_date,
               MIN(rank) as best_rank
        FROM awards
        WHERE ticker = ?
        GROUP BY award_code
        ORDER BY cnt DESC
        """,
        [ticker],
    ).fetchall()
    medal_history = [
        {
            "code": code,
            "name": meta_for(code)["name"],
            "count": int(cnt),
            "latest_date": latest,
            "best_rank": int(best) if best else None,
        }
        for code, cnt, latest, best in med_hist_rows
    ]

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
        medal_history=medal_history,
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


@router.get("/{ticker}/related")
def stock_related(
    ticker: str,
    limit: int = Query(8, ge=1, le=20),
    con: duckdb.DuckDBPyConnection = Depends(get_db),
) -> dict:
    """Find related stocks by (persona match) + (same theme), excluding self.

    Returns two lists: same_persona and same_theme. Each item has ticker + persona + theme.
    """
    ticker = ticker.upper()
    uni = _universe_lookup()
    if ticker not in uni:
        raise HTTPException(404, f"unknown ticker {ticker}")
    info = uni[ticker]
    theme = info.get("theme", "")

    # self persona
    p_row = con.execute(
        "SELECT persona FROM personas WHERE ticker = ?", [ticker]
    ).fetchone()
    self_persona = p_row[0] if p_row else None

    same_persona: list[dict] = []
    if self_persona:
        rows = con.execute(
            """
            SELECT ticker, persona FROM personas
            WHERE persona = ? AND ticker != ?
            ORDER BY ticker
            LIMIT ?
            """,
            [self_persona, ticker, limit],
        ).fetchall()
        for t, persona in rows:
            tinfo = uni.get(t, {})
            same_persona.append(
                {"ticker": t, "persona": persona, "theme": tinfo.get("theme", "")}
            )

    # same theme (from universe)
    same_theme = []
    for t, tinfo in uni.items():
        if t == ticker:
            continue
        if tinfo.get("theme") == theme and theme:
            tp_row = con.execute(
                "SELECT persona FROM personas WHERE ticker = ?", [t]
            ).fetchone()
            same_theme.append(
                {
                    "ticker": t,
                    "persona": tp_row[0] if tp_row else None,
                    "theme": tinfo.get("theme", ""),
                }
            )
    same_theme = sorted(same_theme, key=lambda x: x["ticker"])[:limit]

    return {
        "ticker": ticker,
        "self_persona": self_persona,
        "self_theme": theme,
        "same_persona": same_persona,
        "same_theme": same_theme,
    }
