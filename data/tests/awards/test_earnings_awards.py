"""Tests for earnings awards."""
from datetime import date

import duckdb
import pytest

from data.awards.periodic import earnings_god, earnings_clown
from data.db import init_schema


@pytest.fixture
def con_earnings():
    con = duckdb.connect(":memory:")
    init_schema(con)
    rows = [
        ("AAA", date(2024, 5, 1), date(2024, 3, 31), 1.0, 0.8, 0.2, 25.0, 0.08),
        ("AAA", date(2024, 8, 1), date(2024, 6, 30), 1.1, 1.0, 0.1, 10.0, -0.03),
        ("BBB", date(2024, 5, 2), date(2024, 3, 31), 0.5, 0.6, -0.1, -16.0, -0.10),
        ("CCC", date(2024, 5, 3), date(2024, 3, 31), 2.0, 1.5, 0.5, 33.0, 0.15),
    ]
    con.executemany("INSERT INTO earnings VALUES (?,?,?,?,?,?,?,?)", rows)
    return con


def test_earnings_god_latest_per_ticker(con_earnings):
    res = earnings_god.compute(con_earnings, "ALL", "E")
    # Latest events: AAA 2024-08 (-3%), BBB 2024-05 (-10%), CCC 2024-05 (15%)
    assert res[0][0] == "CCC"
    assert res[0][1] == pytest.approx(0.15)


def test_earnings_clown_latest_per_ticker(con_earnings):
    res = earnings_clown.compute(con_earnings, "ALL", "E")
    assert res[0][0] == "BBB"
    assert res[0][1] == pytest.approx(-0.10)


def test_earnings_god_specific_date(con_earnings):
    res = earnings_god.compute(con_earnings, "2024-05-03", "E")
    assert len(res) == 1
    assert res[0][0] == "CCC"
