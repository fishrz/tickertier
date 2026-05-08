"""🪑 万年老二奖 — most second-place finishes within the period."""
from __future__ import annotations

from data.awards._helpers import parse_period_key


def compute(con, period_key: str, period: str) -> list[tuple[str, float, dict]]:
    start, end = parse_period_key(period, period_key)
    rows = con.execute(
        """
        SELECT ticker, count(*) AS n_silver
        FROM awards
        WHERE period = 'D' AND rank = 2
          AND CAST(period_key AS DATE) BETWEEN ? AND ?
          AND award_code NOT IN ('workhorse', 'silver_curse')
        GROUP BY ticker
        HAVING n_silver > 0
        ORDER BY n_silver DESC
        LIMIT 10
        """,
        [start, end],
    ).fetchall()
    return [(r[0], float(r[1]), {"n_silver": int(r[1])}) for r in rows]
