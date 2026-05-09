"""Portfolio routes."""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_db
from api.models import PortfolioToday, Position

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

PORTFOLIO_PATH = Path(__file__).resolve().parents[2] / "data" / "portfolio.json"


def _load_lottery_tickers() -> dict[str, dict]:
    """Return ticker → {shares, avg_cost} map for lottery positions in portfolio.json."""
    if not PORTFOLIO_PATH.exists():
        return {}
    pf = json.loads(PORTFOLIO_PATH.read_text())
    out: dict[str, dict] = {}
    for p in pf.get("positions", []):
        if p.get("lottery", False):
            out[p["ticker"]] = {
                "shares": float(p["shares"]),
                "avg_cost": float(p.get("avg_cost", 0)),
            }
    return out


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

    # Lottery rows aren't in the positions table — fetch them straight from
    # portfolio.json and join price/tier info ourselves.
    lottery = _load_lottery_tickers()
    lottery_rows = []
    if lottery:
        lt_data = con.execute(
            """
            SELECT pos_t.ticker, pr.close, dm.pct_change, t.tier
            FROM (SELECT UNNEST(?) AS ticker) pos_t
            LEFT JOIN prices pr ON pr.ticker = pos_t.ticker
                AND pr.date = (SELECT MAX(date) FROM prices WHERE ticker = pos_t.ticker)
            LEFT JOIN daily_metrics dm ON dm.ticker = pos_t.ticker AND dm.date = pr.date
            LEFT JOIN tiers t ON t.ticker = pos_t.ticker AND t.date = pr.date
            """,
            [list(lottery.keys())],
        ).fetchall()
        for tk, last_close, pct, tier in lt_data:
            shares = lottery[tk]["shares"]
            avg_cost = lottery[tk]["avg_cost"]
            lottery_rows.append((tk, shares, avg_cost, last_close, pct, tier, True))

    # Tag the regular rows as non-lottery, then merge.
    all_rows = [(*r, False) for r in rows] + lottery_rows

    positions: list[Position] = []
    total_mv = 0.0
    total_upnl = 0.0
    total_today = 0.0
    for tk, shares, avg_cost, last_close, pct, tier, is_lottery in all_rows:
        last_close = float(last_close) if last_close is not None else 0.0
        shares = float(shares)
        avg_cost = float(avg_cost)
        pct = float(pct) if pct is not None else 0.0
        mv = shares * last_close
        upnl = (last_close - avg_cost) * shares
        prev_close = last_close / (1 + pct) if (1 + pct) != 0 else last_close
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
                lottery=is_lottery,
            )
        )
        total_mv += mv
        total_upnl += upnl
        total_today += today_pnl

    # Highlights only consider non-lottery positions.
    pillar = None
    traitor = None
    highlights: dict = {}
    award_pool = [p for p in positions if not p.lottery]
    if award_pool:
        best = max(award_pool, key=lambda p: p.today_pnl)
        worst = min(award_pool, key=lambda p: p.today_pnl)
        pillar = {"ticker": best.ticker, "contribution": best.today_pnl}
        traitor = {"ticker": worst.ticker, "contribution": worst.today_pnl}

        # Cumulative $ winners
        gainers = [p for p in award_pool if p.unrealized_pnl > 0]
        losers = [p for p in award_pool if p.unrealized_pnl < 0]
        cash_king = max(gainers, key=lambda p: p.unrealized_pnl) if gainers else None
        tear_jerker = min(losers, key=lambda p: p.unrealized_pnl) if losers else None

        # Biggest position by market value
        big_pos = max(award_pool, key=lambda p: p.market_value)
        big_pct = (big_pos.market_value / total_mv * 100.0) if total_mv > 0 else 0.0

        # Best buy-in: highest % gain vs avg_cost (only positive)
        priced_in = [p for p in award_pool if p.avg_cost > 0]
        gain_pct = lambda p: (p.last_close - p.avg_cost) / p.avg_cost * 100.0
        priced_gainers = [p for p in priced_in if gain_pct(p) > 0]
        buy_low = max(priced_gainers, key=gain_pct) if priced_gainers else None

        highlights = {
            "pillar": pillar,
            "traitor": traitor,
            "cash_king": (
                {"ticker": cash_king.ticker, "contribution": cash_king.unrealized_pnl}
                if cash_king else None
            ),
            "tear_jerker": (
                {"ticker": tear_jerker.ticker, "contribution": tear_jerker.unrealized_pnl}
                if tear_jerker else None
            ),
            "big_position": {"ticker": big_pos.ticker, "contribution": big_pct},
            "buy_low": (
                {"ticker": buy_low.ticker, "contribution": gain_pct(buy_low)}
                if buy_low else None
            ),
        }

    return PortfolioToday(
        as_of=str(as_of),
        total_market_value=total_mv,
        total_unrealized_pnl=total_upnl,
        today_pnl=total_today,
        pillar=pillar,
        traitor=traitor,
        highlights=highlights,
        positions=positions,
    )
