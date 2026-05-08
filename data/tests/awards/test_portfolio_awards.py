"""Tests for portfolio awards (pillar, traitor)."""
from datetime import date

import duckdb
import pytest

from data.awards.portfolio import pillar, traitor
from data.db import init_schema


@pytest.fixture
def con_portfolio():
    con = duckdb.connect(":memory:")
    init_schema(con)
    # Two days of prices for AAA, BBB, CCC
    d1, d2 = date(2024, 6, 3), date(2024, 6, 4)
    prices = [
        ("AAA", d1, 100, 100, 100, 100, 100, 1000),
        ("AAA", d2, 100, 110, 100, 110, 110, 1000),  # +10
        ("BBB", d1, 50, 50, 50, 50, 50, 1000),
        ("BBB", d2, 50, 50, 40, 45, 45, 1000),  # -5
        ("CCC", d1, 200, 200, 200, 200, 200, 1000),
        ("CCC", d2, 200, 200, 200, 200, 200, 1000),  # 0
    ]
    con.executemany("INSERT INTO prices VALUES (?,?,?,?,?,?,?,?)", prices)
    pos = [
        (d1, "AAA", 10, 100),
        (d1, "BBB", 20, 50),
        (d1, "CCC", 5, 200),
    ]
    con.executemany("INSERT INTO positions VALUES (?,?,?,?)", pos)
    return con


def test_pillar_picks_biggest_positive_pnl(con_portfolio):
    res = pillar.compute(con_portfolio, "2024-06-04", "D")
    assert res[0][0] == "AAA"
    assert res[0][1] == pytest.approx(10 * 10)
    tickers = [r[0] for r in res]
    assert "BBB" not in tickers
    assert "CCC" not in tickers  # zero pnl excluded


def test_traitor_picks_biggest_negative_pnl(con_portfolio):
    res = traitor.compute(con_portfolio, "2024-06-04", "D")
    assert res[0][0] == "BBB"
    assert res[0][1] == pytest.approx(20 * -5)
