"""📈 暴兵奖 — positive day with biggest volume surge."""
from __future__ import annotations


def compute(con, period_key: str, period: str = "D") -> list[tuple[str, float, dict]]:
    rows = con.execute(
        """
        SELECT ticker, vol_ratio_20, pct_change
        FROM daily_metrics
        WHERE date = ?
          AND pct_change > 0
          AND vol_ratio_20 IS NOT NULL
        ORDER BY vol_ratio_20 DESC
        LIMIT 10
        """,
        [period_key],
    ).fetchall()
    return [(r[0], float(r[1]), {"pct_change": r[2]}) for r in rows]
