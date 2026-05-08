"""Tier calculator: assign a daily tier to each ticker based on a composite z-score."""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def _bucket(rank_pct: float) -> str:
    if rank_pct <= 0.05:
        return "🔥 夯死了"
    if rank_pct <= 0.20:
        return "👑 顶级"
    if rank_pct <= 0.50:
        return "💪 人上人"
    if rank_pct <= 0.80:
        return "😐 NPC"
    return "💩 拉完了"


def compute_tiers(con, date_str: str) -> int:
    """For the given trading day, compute and upsert tier rows. Returns row count."""
    # Fetch QQQ pct_change for the override
    q = con.execute(
        "SELECT pct_change FROM daily_metrics WHERE ticker='QQQ' AND date = ?",
        [date_str],
    ).fetchone()
    qqq_pct = float(q[0]) if (q and q[0] is not None) else None

    rows = con.execute(
        """
        WITH d AS (
          SELECT ticker, pct_change, intraday_amp, vol_ratio_20, rebound, fade
          FROM daily_metrics
          WHERE date = ? AND ticker != 'QQQ' AND pct_change IS NOT NULL
        ),
        stats AS (
          SELECT
            avg(pct_change) AS mu_p, stddev_samp(pct_change) AS sd_p,
            avg(intraday_amp) AS mu_a, stddev_samp(intraday_amp) AS sd_a,
            avg(vol_ratio_20) AS mu_v, stddev_samp(vol_ratio_20) AS sd_v,
            avg(rebound - abs(fade)) AS mu_r, stddev_samp(rebound - abs(fade)) AS sd_r
          FROM d
        )
        SELECT d.ticker, d.pct_change,
          0.6 * (d.pct_change - s.mu_p) / NULLIF(s.sd_p, 0)
          + 0.2 * (COALESCE(d.intraday_amp, s.mu_a) - s.mu_a) / NULLIF(s.sd_a, 0)
          + 0.1 * (COALESCE(d.vol_ratio_20, s.mu_v) - s.mu_v) / NULLIF(s.sd_v, 0)
          + 0.1 * ((COALESCE(d.rebound,0) - abs(COALESCE(d.fade,0))) - s.mu_r) / NULLIF(s.sd_r, 0)
            AS score
        FROM d, stats s
        """,
        [date_str],
    ).fetchall()

    if not rows:
        return 0

    # Rank by score descending → rank_pct = (rank-1)/(n-1)
    scored = [(t, p, (s if s is not None else 0.0)) for t, p, s in rows]
    scored.sort(key=lambda x: x[2], reverse=True)
    n = len(scored)
    out = []
    for i, (t, pct, score) in enumerate(scored):
        rank_pct = i / (n - 1) if n > 1 else 0.0
        tier = _bucket(rank_pct)
        # 答辩 override
        if pct is not None and pct < -0.05:
            if qqq_pct is None or (pct - qqq_pct) < -0.03:
                tier = "☠️ 答辩"
        out.append((t, date_str, tier, score, rank_pct))

    con.execute("DELETE FROM tiers WHERE date = ?", [date_str])
    con.executemany(
        "INSERT INTO tiers (ticker, date, tier, score, rank_pct) VALUES (?, ?, ?, ?, ?)",
        out,
    )
    return len(out)
