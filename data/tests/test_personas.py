"""Tests for persona clustering."""
from __future__ import annotations

import json

import duckdb
import pytest

from data.db import init_schema, get_conn
from data.personas import TIERS, compute_personas


def _seed(con: duckdb.DuckDBPyConnection) -> None:
    init_schema(con)
    rows = []
    # 5 tickers mostly 🔥, 5 mostly 😐, 5 mostly 💩
    patterns = [
        (["A1", "A2", "A3", "A4", "A5"], "🔥 夯死了"),
        (["B1", "B2", "B3", "B4", "B5"], "😐 NPC"),
        (["C1", "C2", "C3", "C4", "C5"], "💩 拉完了"),
    ]
    from datetime import date, timedelta
    base = date(2024, 1, 1)
    for tks, dom in patterns:
        for tk in tks:
            for i in range(50):
                rows.append((tk, base + timedelta(days=i), dom, 0.0, 0.0))
            # one off-tier day to avoid degenerate
            rows.append((tk, base + timedelta(days=51), "👑 顶级", 0.0, 0.0))
    con.executemany(
        "INSERT INTO tiers (ticker, date, tier, score, rank_pct) VALUES (?, ?, ?, ?, ?)", rows
    )


def test_compute_personas_synthetic(tmp_path):
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    _seed(con)
    n = compute_personas(con, k=3)
    assert n == 15
    rows = con.execute("SELECT ticker, persona, tier_dist FROM personas").fetchall()
    assert len(rows) == 15
    for tk, persona, dist_json in rows:
        assert persona  # not empty
        d = json.loads(dist_json)
        assert set(d.keys()) == set(TIERS)
        assert abs(sum(d.values()) - 1.0) < 1e-6
    con.close()


@pytest.mark.integration
@pytest.mark.skipif(not __import__("os").environ.get("INTEGRATION"), reason="set INTEGRATION=1 to run")
def test_compute_personas_real_db():
    con = get_conn(read_only=True)
    try:
        n = con.execute("SELECT COUNT(*) FROM personas").fetchone()[0]
        assert n == 81, f"expected 81 personas, got {n}"
        # all tickers should have non-empty persona
        bad = con.execute("SELECT COUNT(*) FROM personas WHERE persona IS NULL OR persona = ''").fetchone()[0]
        assert bad == 0
    finally:
        con.close()
