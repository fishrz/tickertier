"""🛡️ 抗揍奖 — best relative performer on a QQQ-down day.

Skips (returns []) if QQQ data is missing for the day, or if QQQ is not
sufficiently down (QQQ pct_change >= -0.5%).
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def compute(con, period_key: str, period: str = "D") -> list[tuple[str, float, dict]]:
    qqq = con.execute(
        """
        SELECT pct_change FROM daily_metrics
        WHERE ticker='QQQ' AND date = ?
        """,
        [period_key],
    ).fetchone()
    if not qqq or qqq[0] is None:
        log.info("tank: QQQ data missing for %s, skipping", period_key)
        return []
    qqq_pct = float(qqq[0])
    if qqq_pct >= -0.005:
        return []
    rows = con.execute(
        """
        SELECT ticker, pct_change
        FROM daily_metrics
        WHERE date = ? AND ticker != 'QQQ' AND pct_change IS NOT NULL
        ORDER BY pct_change DESC
        LIMIT 10
        """,
        [period_key],
    ).fetchall()
    return [(r[0], float(r[1]), {"qqq_pct": qqq_pct}) for r in rows]
