"""🏆 今日股王 — biggest daily winner."""
from __future__ import annotations


def compute(con, period_key: str, period: str = "D") -> list[tuple[str, float, dict]]:
    rows = con.execute(
        """
        SELECT ticker, pct_change, intraday_amp, vol_ratio_20
        FROM daily_metrics
        WHERE date = ? AND pct_change IS NOT NULL
        ORDER BY pct_change DESC
        LIMIT 10
        """,
        [period_key],
    ).fetchall()
    return [
        (r[0], float(r[1]), {"intraday_amp": r[2], "vol_ratio_20": r[3]}) for r in rows
    ]
