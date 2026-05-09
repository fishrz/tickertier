"""🧠 人间清醒奖 — best entry: avg_cost lowest vs last_close (biggest % discount)."""
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
        )
        SELECT pos.ticker,
               (latest.close - pos.avg_cost) / pos.avg_cost * 100.0 AS gain_pct,
               pos.shares,
               pos.avg_cost,
               latest.close
        FROM pos JOIN latest ON latest.ticker = pos.ticker
        WHERE pos.avg_cost > 0
        ORDER BY gain_pct DESC
        LIMIT 10
        """,
        [period_key],
    ).fetchall()
    pos_rows = [r for r in rows if r[1] is not None and r[1] > 0]
    return [
        (r[0], float(r[1]), {
            "shares": r[2], "avg_cost": r[3], "last_close": r[4],
        })
        for r in pos_rows
    ]
