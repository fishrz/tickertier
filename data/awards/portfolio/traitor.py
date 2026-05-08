"""🩸 拖后腿奖 — biggest negative shares × Δprice contribution on a day."""
from __future__ import annotations


def compute(con, period_key: str, period: str = "D") -> list[tuple[str, float, dict]]:
    rows = con.execute(
        """
        WITH pos AS (
          SELECT ticker, shares
          FROM positions
          WHERE date = (SELECT max(date) FROM positions WHERE date <= ?)
        )
        SELECT p.ticker,
               pos.shares * (p.close - lag_close.prev) AS pnl,
               pos.shares,
               p.close - lag_close.prev AS d_price
        FROM prices p
        JOIN pos ON pos.ticker = p.ticker
        JOIN (
          SELECT ticker, close AS prev FROM prices
          WHERE date = (SELECT max(date) FROM prices WHERE date < ?)
        ) lag_close ON lag_close.ticker = p.ticker
        WHERE p.date = ?
        ORDER BY pnl ASC
        LIMIT 10
        """,
        [period_key, period_key, period_key],
    ).fetchall()
    neg_rows = [r for r in rows if r[1] is not None and r[1] < 0]
    return [
        (r[0], float(r[1]), {"shares": r[2], "d_price": r[3]}) for r in neg_rows
    ]
