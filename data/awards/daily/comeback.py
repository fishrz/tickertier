"""🪄 绝地翻身奖 — closed near high after touching low (positive day, big rebound)."""
from __future__ import annotations


def compute(con, period_key: str, period: str = "D") -> list[tuple[str, float, dict]]:
    rows = con.execute(
        """
        SELECT ticker, rebound, pct_change, fade
        FROM daily_metrics
        WHERE date = ? AND pct_change > 0 AND rebound IS NOT NULL
        ORDER BY rebound DESC
        LIMIT 10
        """,
        [period_key],
    ).fetchall()
    return [(r[0], float(r[1]), {"pct_change": r[2], "fade": r[3]}) for r in rows]
