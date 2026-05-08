"""🎭 影帝奖 — high open, low close (positive gap, biggest fade)."""
from __future__ import annotations


def compute(con, period_key: str, period: str = "D") -> list[tuple[str, float, dict]]:
    rows = con.execute(
        """
        SELECT ticker, fade, gap, pct_change
        FROM daily_metrics
        WHERE date = ? AND gap > 0 AND fade IS NOT NULL
        ORDER BY fade ASC
        LIMIT 10
        """,
        [period_key],
    ).fetchall()
    return [(r[0], float(r[1]), {"gap": r[2], "pct_change": r[3]}) for r in rows]
