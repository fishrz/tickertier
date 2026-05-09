"""😭 我的眼泪奖 — biggest cumulative unrealized LOSS since cost basis."""
from __future__ import annotations


def compute(con, period_key: str, period: str = "D") -> list[tuple[str, float, dict]]:
    rows = con.execute(
        """
        WITH pos AS (
          SELECT ticker, shares, avg_cost
          FROM positions
          WHERE date = (SELECT max(date) FROM positions WHERE date <= ?)
        )
        SELECT pos.ticker,
               (p.close - pos.avg_cost) * pos.shares AS upnl,
               pos.shares,
               pos.avg_cost,
               p.close AS last_close
        FROM prices p
        JOIN pos ON pos.ticker = p.ticker
        WHERE p.date = (SELECT max(date) FROM prices WHERE ticker = p.ticker)
        ORDER BY upnl ASC
        LIMIT 10
        """,
        [period_key],
    ).fetchall()
    neg_rows = [r for r in rows if r[1] is not None and r[1] < 0]
    return [
        (r[0], float(r[1]), {
            "shares": r[2], "avg_cost": r[3], "last_close": r[4],
        })
        for r in neg_rows
    ]
