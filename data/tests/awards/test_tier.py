"""Tests for tier calculator."""
import pytest

from data.awards.tier import compute_tiers


def test_compute_tiers_assigns_buckets(con_metrics):
    n = compute_tiers(con_metrics, "2024-06-03")
    assert n == 7  # excludes QQQ
    rows = con_metrics.execute(
        "SELECT ticker, tier, score, rank_pct FROM tiers WHERE date='2024-06-03' ORDER BY score DESC"
    ).fetchall()
    # Top should be 🔥 夯死了 or 👑 顶级
    assert rows[0][1] in ("🔥 夯死了", "👑 顶级")
    # BBB had pct=-8% and qqq=-1.2% → diff = -6.8% < -3% → 答辩 override
    bbb = [r for r in rows if r[0] == "BBB"][0]
    assert bbb[1] == "☠️ 答辩"


def test_compute_tiers_empty_day(con_metrics):
    n = compute_tiers(con_metrics, "2030-01-01")
    assert n == 0
