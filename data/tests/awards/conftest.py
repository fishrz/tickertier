"""Shared fixtures for award tests."""
from __future__ import annotations

from datetime import date, timedelta

import duckdb
import pandas as pd
import pytest

from data.db import init_schema


def _make_metrics_rows(spec: list[tuple]) -> pd.DataFrame:
    """spec rows: (ticker, date, pct_change, intraday_amp, gap, rebound, fade, vol_ratio_20, std_5)."""
    return pd.DataFrame(
        spec,
        columns=[
            "ticker", "date", "pct_change", "intraday_amp", "gap",
            "rebound", "fade", "vol_ratio_20", "std_5",
        ],
    )


@pytest.fixture
def con_metrics():
    """A fresh in-memory DB with handcrafted daily_metrics for date 2024-06-03."""
    con = duckdb.connect(":memory:")
    init_schema(con)
    d = date(2024, 6, 3)
    rows = [
        # ticker, date, pct, amp, gap, rebound, fade, vol_ratio, std_5
        ("AAA", d, 0.10, 0.12, 0.02, 0.11, -0.01, 1.5, 1.0),  # king candidate
        ("BBB", d, -0.08, 0.15, 0.03, 0.01, -0.10, 2.0, 1.0),  # clown / oscar candidate
        ("CCC", d, 0.05, 0.20, -0.01, 0.20, 0.0, 3.0, 1.0),    # roller_coaster + pump_army
        ("DDD", d, 0.001, 0.005, 0.0, 0.002, -0.001, 0.5, 1.0),  # npc_god
        ("EEE", d, 0.02, 0.08, 0.05, 0.07, -0.02, 1.1, 1.0),   # oscar (gap>0, faded)
        ("FFF", d, 0.03, 0.10, -0.02, 0.10, 0.0, 1.0, 1.0),    # comeback (pct>0, big rebound)
        ("GGG", d, -0.02, 0.04, -0.01, 0.01, -0.02, 0.6, 1.0),  # mild loser
        ("QQQ", d, -0.012, 0.015, -0.005, 0.0, -0.012, 1.0, 1.0),  # benchmark down
    ]
    con.register("_m", _make_metrics_rows(rows))
    con.execute("INSERT INTO daily_metrics SELECT * FROM _m")
    con.unregister("_m")
    return con
