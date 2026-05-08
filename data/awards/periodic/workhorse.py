"""🏅 劳模奖 — most awards earned within the period (meta-award).

Counts daily awards (period='D') whose date falls in the parent period range.
"""
from __future__ import annotations

from data.awards._helpers import parse_period_key


def compute(con, period_key: str, period: str) -> list[tuple[str, float, dict]]:
    start, end = parse_period_key(period, period_key)
    rows = con.execute(
        """
        SELECT ticker, count(*) AS n_awards
        FROM awards
        WHERE period = 'D'
          AND CAST(period_key AS DATE) BETWEEN ? AND ?
          AND award_code != 'workhorse'
          AND award_code != 'silver_curse'
        GROUP BY ticker
        HAVING n_awards > 0
        ORDER BY n_awards DESC
        LIMIT 10
        """,
        [start, end],
    ).fetchall()
    return [(r[0], float(r[1]), {"n_awards": int(r[1])}) for r in rows]
