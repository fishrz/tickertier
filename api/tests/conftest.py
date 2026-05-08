"""Shared API test fixtures with a tiny synthetic DB."""
from __future__ import annotations

import json
from datetime import date, timedelta

import duckdb
import pytest
from fastapi.testclient import TestClient

from api import deps
from api.main import app
from data.db import init_schema


@pytest.fixture
def fake_db(tmp_path, monkeypatch):
    p = tmp_path / "test.duckdb"
    con = duckdb.connect(str(p))
    init_schema(con)

    today = date(2026, 5, 8)
    yday = today - timedelta(days=1)
    tickers = ["NVDA", "AMD", "TSM", "ASML", "MU"]
    # prices: 60 days of synthetic data
    rows_p = []
    rows_dm = []
    rows_t = []
    for i, tk in enumerate(tickers):
        base = 100.0 + i * 10
        for d_off in range(60):
            d = today - timedelta(days=59 - d_off)
            close = base * (1.0 + 0.001 * d_off + 0.002 * i)
            rows_p.append((tk, d, close * 0.99, close * 1.01, close * 0.98, close, close, 1_000_000))
            pct = 0.5 + i * 0.1
            rows_dm.append((tk, d, pct, 0.02, 0.0, 0.0, 0.0, 1.0, 0.01))
            tier = ["🔥 夯死了", "💪 人上人", "😐 NPC", "💩 拉完了", "👑 顶级"][i]
            rows_t.append((tk, d, tier, float(i), 0.5))
    con.executemany(
        "INSERT INTO prices (ticker, date, open, high, low, close, adj_close, volume) VALUES (?,?,?,?,?,?,?,?)",
        rows_p,
    )
    con.executemany(
        "INSERT INTO daily_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows_dm,
    )
    con.executemany(
        "INSERT INTO tiers VALUES (?, ?, ?, ?, ?)",
        rows_t,
    )

    # awards: a few daily and yearly
    award_rows = [
        ("daily_king", "D", str(today), 1, "NVDA", 5.5, json.dumps({"intraday_amp": 0.05})),
        ("daily_king", "D", str(today), 2, "AMD", 4.0, "{}"),
        ("daily_king", "D", str(today), 3, "TSM", 3.0, "{}"),
        ("daily_clown", "D", str(today), 1, "ASML", -3.0, "{}"),
        ("daily_king", "D", str(yday), 1, "AMD", 4.5, "{}"),
        ("workhorse", "Y", "2026", 1, "NVDA", 10, "{}"),
        ("workhorse", "Y", "2026", 2, "TSM", 8, "{}"),
        ("pillar", "D", str(today), 1, "NVDA", 100.0, "{}"),
        ("traitor", "D", str(today), 1, "MU", -50.0, "{}"),
    ]
    con.executemany("INSERT INTO awards VALUES (?, ?, ?, ?, ?, ?, ?)", award_rows)

    # personas
    pers_rows = [
        (tk, ["夯系顶流", "蒸蒸日上", "NPC 系", "长期病号", "老油条"][i],
         json.dumps({"🔥 夯死了": 0.5, "👑 顶级": 0.1, "💪 人上人": 0.1, "😐 NPC": 0.1, "💩 拉完了": 0.1, "☠️ 答辩": 0.1}),
         "2026-05-08 00:00:00")
        for i, tk in enumerate(tickers)
    ]
    con.executemany("INSERT INTO personas VALUES (?, ?, ?, ?)", pers_rows)

    # positions
    pos_rows = [
        (today, "NVDA", 50.0, 100.0),
        (today, "AMD", 20.0, 110.0),
    ]
    con.executemany("INSERT INTO positions VALUES (?, ?, ?, ?)", pos_rows)
    con.close()

    def _override():
        c = duckdb.connect(str(p), read_only=True)
        try:
            yield c
        finally:
            c.close()

    app.dependency_overrides[deps.get_db] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()
