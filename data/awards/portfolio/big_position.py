"""👑 仓位之王 — biggest market value share of the portfolio."""
from __future__ import annotations


def compute(con, period_key: str, period: str = "D") -> list[tuple[str, float, dict]]:
    rows = con.execute(
        """
        WITH pos AS (
          SELECT ticker, shares, avg_cost
          FROM positions
          WHERE date = (SELECT max(date) FROM positions WHERE date <= ?)
        ),
        latest AS (
          SELECT p.ticker, p.close
          FROM prices p
          WHERE p.date = (SELECT max(date) FROM prices WHERE ticker = p.ticker)
        ),
        mv AS (
          SELECT pos.ticker,
                 pos.shares * latest.close AS market_value,
                 pos.shares,
                 latest.close
          FROM pos JOIN latest ON latest.ticker = pos.ticker
        ),
        total AS (SELECT SUM(market_value) AS tot FROM mv)
        SELECT mv.ticker,
               mv.market_value / total.tot * 100.0 AS weight_pct,
               mv.shares,
               mv.close,
               mv.market_value
        FROM mv, total
        WHERE total.tot > 0
        ORDER BY weight_pct DESC
        LIMIT 10
        """,
        [period_key],
    ).fetchall()
    return [
        (r[0], float(r[1]), {
            "shares": r[2], "last_close": r[3], "market_value": r[4],
        })
        for r in rows if r[1] is not None
    ]
