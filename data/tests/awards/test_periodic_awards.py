"""Tests for periodic awards (reverse_idx, steady_grind, gambler, workhorse, silver_curse)."""
from datetime import date, timedelta

import duckdb
import pandas as pd
import pytest

from data.awards.periodic import (
    reverse_idx, steady_grind, gambler, workhorse, silver_curse,
)
from data.db import init_schema


@pytest.fixture
def con_period():
    con = duckdb.connect(":memory:")
    init_schema(con)
    # Build 10 trading days starting 2024-06-03 (Monday)
    start = date(2024, 6, 3)
    days = [start + timedelta(days=i) for i in range(10)]
    rows = []
    # QQQ: alternating returns
    qqq_rets = [-0.01, 0.02, -0.005, 0.015, -0.02, 0.01, -0.005, 0.005, -0.01, 0.005]
    # AAA: anti-correlated with QQQ → reverse_idx winner
    aaa_rets = [-r * 1.0 + 0.001 for r in qqq_rets]
    # BBB: very steady positive with tiny jitter (Sharpe winner)
    bbb_rets = [0.005, 0.006, 0.005, 0.006, 0.005, 0.006, 0.005, 0.006, 0.005, 0.006]
    # CCC: huge swings (gambler winner)
    ccc_rets = [0.05, -0.05, 0.05, -0.05, 0.05, -0.05, 0.05, -0.05, 0.05, -0.05]

    for i, d in enumerate(days):
        rows.append(("QQQ", d, qqq_rets[i], abs(qqq_rets[i]) + 0.005, 0, 0, 0, 1, 0))
        rows.append(("AAA", d, aaa_rets[i], 0.02, 0, 0, 0, 1, 0))
        rows.append(("BBB", d, bbb_rets[i], 0.01, 0, 0, 0, 1, 0))
        rows.append(("CCC", d, ccc_rets[i], 0.10, 0, 0, 0, 1, 0))

    df = pd.DataFrame(rows, columns=[
        "ticker", "date", "pct_change", "intraday_amp", "gap",
        "rebound", "fade", "vol_ratio_20", "std_5",
    ])
    con.register("_m", df)
    con.execute("INSERT INTO daily_metrics SELECT * FROM _m")
    con.unregister("_m")
    return con


def test_reverse_idx_picks_anticorrelated(con_period):
    res = reverse_idx.compute(con_period, "2024-W23", "W")
    assert res, "expected results for week 23 of 2024"
    assert res[0][0] == "AAA"
    assert res[0][1] > 0.5


def test_steady_grind_picks_constant_positive(con_period):
    res = steady_grind.compute(con_period, "2024-06", "M")
    assert res[0][0] == "BBB"


def test_gambler_picks_biggest_amp(con_period):
    res = gambler.compute(con_period, "2024-06", "M")
    assert res[0][0] == "CCC"
    assert res[0][1] == pytest.approx(10 * 0.10)


def test_workhorse_counts_awards():
    con = duckdb.connect(":memory:")
    init_schema(con)
    # Insert synthetic awards for June 2024
    con.execute("INSERT INTO awards VALUES ('daily_king','D','2024-06-03',1,'AAA',0.1,'{}')")
    con.execute("INSERT INTO awards VALUES ('daily_king','D','2024-06-04',1,'AAA',0.1,'{}')")
    con.execute("INSERT INTO awards VALUES ('roller_coaster','D','2024-06-04',1,'BBB',0.1,'{}')")
    res = workhorse.compute(con, "2024-06", "M")
    assert res[0][0] == "AAA"
    assert int(res[0][1]) == 2


def test_silver_curse_counts_rank2():
    con = duckdb.connect(":memory:")
    init_schema(con)
    con.execute("INSERT INTO awards VALUES ('daily_king','D','2024-06-03',2,'BBB',0.1,'{}')")
    con.execute("INSERT INTO awards VALUES ('roller_coaster','D','2024-06-03',2,'BBB',0.1,'{}')")
    con.execute("INSERT INTO awards VALUES ('daily_king','D','2024-06-04',1,'AAA',0.1,'{}')")
    res = silver_curse.compute(con, "2024-06", "M")
    assert res[0][0] == "BBB"
    assert int(res[0][1]) == 2
