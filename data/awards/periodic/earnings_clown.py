"""💼 财报现形 — biggest negative next-day reaction to earnings."""
from __future__ import annotations


def compute(con, period_key: str, period: str = "E") -> list[tuple[str, float, dict]]:
    if period_key == "ALL":
        rows = con.execute(
            """
            WITH latest AS (
              SELECT ticker, max(report_date) AS rd
              FROM earnings WHERE next_day_pct IS NOT NULL
              GROUP BY ticker
            )
            SELECT e.ticker, e.next_day_pct, e.report_date, e.surprise_pct
            FROM earnings e
            JOIN latest l ON l.ticker = e.ticker AND l.rd = e.report_date
            WHERE e.next_day_pct IS NOT NULL
            ORDER BY e.next_day_pct ASC
            LIMIT 10
            """
        ).fetchall()
    else:
        rows = con.execute(
            """
            SELECT ticker, next_day_pct, report_date, surprise_pct
            FROM earnings
            WHERE report_date = ? AND next_day_pct IS NOT NULL
            ORDER BY next_day_pct ASC
            LIMIT 10
            """,
            [period_key],
        ).fetchall()
    return [
        (r[0], float(r[1]), {"report_date": str(r[2]), "surprise_pct": r[3]})
        for r in rows
    ]
