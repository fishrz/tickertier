"""Portfolio routes."""
from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_db
from api.models import PortfolioToday, Position

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/today", response_model=PortfolioToday)
def portfolio_today(con: duckdb.DuckDBPyConnection = Depends(get_db)) -> PortfolioToday:
    as_of_row = con.execute("SELECT MAX(date) FROM positions").fetchone()
    if not as_of_row or not as_of_row[0]:
        raise HTTPException(404, "no positions")
    as_of = as_of_row[0]

    rows = con.execute(
        """
        SELECT pos.ticker, pos.shares, pos.avg_cost,
               pr.close AS last_close,
               dm.pct_change,
               t.tier
        FROM positions pos
        LEFT JOIN prices pr ON pr.ticker = pos.ticker
            AND pr.date = (SELECT MAX(date) FROM prices WHERE ticker = pos.ticker)
        LEFT JOIN daily_metrics dm ON dm.ticker = pos.ticker AND dm.date = pr.date
        LEFT JOIN tiers t ON t.ticker = pos.ticker AND t.date = pr.date
        WHERE pos.date = ?
        ORDER BY pos.ticker
        """,
        [as_of],
    ).fetchall()

    positions: list[Position] = []
    total_mv = 0.0
    total_upnl = 0.0
    total_today = 0.0
    for tk, shares, avg_cost, last_close, pct, tier in rows:
        last_close = float(last_close) if last_close is not None else 0.0
        shares = float(shares)
        avg_cost = float(avg_cost)
        pct = float(pct) if pct is not None else 0.0
        mv = shares * last_close
        upnl = (last_close - avg_cost) * shares
        # today_pnl: shares * (last_close - prev_close) ≈ mv * pct/(100+pct), but use direct:
        prev_close = last_close / (1 + pct / 100.0) if (1 + pct / 100.0) != 0 else last_close
        today_pnl = (last_close - prev_close) * shares
        positions.append(
            Position(
                ticker=tk,
                shares=shares,
                avg_cost=avg_cost,
                last_close=last_close,
                market_value=mv,
                unrealized_pnl=upnl,
                today_pnl=today_pnl,
                today_pct=pct,
                tier_today=tier,
            )
        )
        total_mv += mv
        total_upnl += upnl
        total_today += today_pnl

    pillar = None
    traitor = None
    if positions:
        best = max(positions, key=lambda p: p.today_pnl)
        worst = min(positions, key=lambda p: p.today_pnl)
        pillar = {"ticker": best.ticker, "contribution": best.today_pnl}
        traitor = {"ticker": worst.ticker, "contribution": worst.today_pnl}

    return PortfolioToday(
        as_of=str(as_of),
        total_market_value=total_mv,
        total_unrealized_pnl=total_upnl,
        today_pnl=total_today,
        pillar=pillar,
        traitor=traitor,
        positions=positions,
    )
