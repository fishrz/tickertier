"""Compute derived daily metrics from the prices table."""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)

_METRICS_SQL = """
WITH base AS (
  SELECT
    ticker, date, open, high, low, close, volume,
    LAG(close) OVER (PARTITION BY ticker ORDER BY date) AS prev_close,
    AVG(volume) OVER (
      PARTITION BY ticker ORDER BY date
      ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) AS sma20_vol,
    STDDEV_SAMP(close) OVER (
      PARTITION BY ticker ORDER BY date
      ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS std_5
  FROM prices
)
SELECT
  ticker,
  date,
  CASE WHEN prev_close IS NULL OR prev_close = 0 THEN NULL
       ELSE (close - prev_close) / prev_close END AS pct_change,
  CASE WHEN prev_close IS NULL OR prev_close = 0 THEN NULL
       ELSE (high - low) / prev_close END AS intraday_amp,
  CASE WHEN prev_close IS NULL OR prev_close = 0 THEN NULL
       ELSE (open - prev_close) / prev_close END AS gap,
  (close - low) / NULLIF(low, 0) AS rebound,
  (close - high) / NULLIF(high, 0) AS fade,
  CASE WHEN sma20_vol IS NULL OR sma20_vol = 0 THEN NULL
       ELSE volume / sma20_vol END AS vol_ratio_20,
  std_5
FROM base
"""


def compute_metrics(con) -> int:
    """Rebuild daily_metrics from prices using SQL window functions.

    Returns the number of rows written.

    Example:
        >>> from data.db import get_conn, init_schema
        >>> con = get_conn()  # doctest: +SKIP
        >>> compute_metrics(con)  # doctest: +SKIP
    """
    con.execute("DELETE FROM daily_metrics")
    con.execute(f"INSERT INTO daily_metrics {_METRICS_SQL}")
    n = con.execute("SELECT count(*) FROM daily_metrics").fetchone()[0]
    log.info("compute_metrics: wrote %d rows", n)
    return int(n)
