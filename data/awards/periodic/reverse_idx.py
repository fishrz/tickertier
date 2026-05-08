"""🪦 反指奖 — strongest correlation with QQQ negative return over a period."""
from __future__ import annotations

import logging

from data.awards._helpers import parse_period_key

log = logging.getLogger(__name__)


def compute(con, period_key: str, period: str) -> list[tuple[str, float, dict]]:
    start, end = parse_period_key(period, period_key)
    qqq_count = con.execute(
        "SELECT count(*) FROM daily_metrics WHERE ticker='QQQ' AND date BETWEEN ? AND ?",
        [start, end],
    ).fetchone()[0]
    if qqq_count < 3:
        log.info("reverse_idx: QQQ data insufficient for %s/%s", period, period_key)
        return []
    rows = con.execute(
        """
        WITH q AS (
          SELECT date, pct_change AS q_pct
          FROM daily_metrics
          WHERE ticker='QQQ' AND date BETWEEN ? AND ? AND pct_change IS NOT NULL
        ),
        joined AS (
          SELECT m.ticker, m.date, m.pct_change AS t_pct, q.q_pct
          FROM daily_metrics m
          JOIN q ON q.date = m.date
          WHERE m.ticker != 'QQQ' AND m.pct_change IS NOT NULL
        )
        SELECT ticker,
               corr(t_pct, -q_pct) AS rev_corr,
               count(*) AS n
        FROM joined
        GROUP BY ticker
        HAVING n >= 3 AND rev_corr IS NOT NULL
        ORDER BY rev_corr DESC
        LIMIT 10
        """,
        [start, end],
    ).fetchall()
    return [(r[0], float(r[1]), {"n": int(r[2])}) for r in rows]
