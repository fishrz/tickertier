"""💤 NPC 之光 — smallest intraday amplitude with low relative volume."""
from __future__ import annotations


def compute(con, period_key: str, period: str = "D") -> list[tuple[str, float, dict]]:
    rows = con.execute(
        """
        SELECT ticker, intraday_amp, vol_ratio_20, pct_change
        FROM daily_metrics
        WHERE date = ?
          AND intraday_amp IS NOT NULL
          AND vol_ratio_20 IS NOT NULL
          AND vol_ratio_20 < 0.7
        ORDER BY intraday_amp ASC
        LIMIT 10
        """,
        [period_key],
    ).fetchall()
    return [
        (r[0], float(r[1]), {"vol_ratio_20": r[2], "pct_change": r[3]}) for r in rows
    ]
