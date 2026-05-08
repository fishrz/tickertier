"""🎰 赌狗之友奖 — sum of intraday amplitudes over period."""
from __future__ import annotations

from data.awards._helpers import parse_period_key


def compute(con, period_key: str, period: str) -> list[tuple[str, float, dict]]:
    start, end = parse_period_key(period, period_key)
    rows = con.execute(
        """
        SELECT ticker, sum(intraday_amp) AS total_amp, count(*) AS n
        FROM daily_metrics
        WHERE date BETWEEN ? AND ? AND intraday_amp IS NOT NULL AND ticker != 'QQQ'
        GROUP BY ticker
        HAVING n >= 1
        ORDER BY total_amp DESC
        LIMIT 10
        """,
        [start, end],
    ).fetchall()
    return [(r[0], float(r[1]), {"n": int(r[2])}) for r in rows]
