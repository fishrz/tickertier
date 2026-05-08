"""🎢 过山车之王 — biggest intraday amplitude."""
from __future__ import annotations


def compute(con, period_key: str, period: str = "D") -> list[tuple[str, float, dict]]:
    rows = con.execute(
        """
        SELECT ticker, intraday_amp, pct_change
        FROM daily_metrics
        WHERE date = ? AND intraday_amp IS NOT NULL
        ORDER BY intraday_amp DESC
        LIMIT 10
        """,
        [period_key],
    ).fetchall()
    return [(r[0], float(r[1]), {"pct_change": r[2]}) for r in rows]
