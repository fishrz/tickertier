"""🐢 细水长流奖 — highest Sharpe ratio (mean/std of daily returns) over period."""
from __future__ import annotations

from data.awards._helpers import parse_period_key


def compute(con, period_key: str, period: str) -> list[tuple[str, float, dict]]:
    start, end = parse_period_key(period, period_key)
    rows = con.execute(
        """
        SELECT ticker,
               CASE WHEN stddev_samp(pct_change) IS NULL OR stddev_samp(pct_change) = 0
                    THEN NULL
                    ELSE avg(pct_change) / stddev_samp(pct_change) END AS sharpe,
               avg(pct_change) AS mean_ret,
               stddev_samp(pct_change) AS std_ret,
               count(*) AS n
        FROM daily_metrics
        WHERE date BETWEEN ? AND ? AND pct_change IS NOT NULL AND ticker != 'QQQ'
        GROUP BY ticker
        HAVING n >= 5 AND sharpe IS NOT NULL
        ORDER BY sharpe DESC
        LIMIT 10
        """,
        [start, end],
    ).fetchall()
    return [
        (r[0], float(r[1]), {"mean_ret": r[2], "std_ret": r[3], "n": int(r[4])})
        for r in rows
    ]
