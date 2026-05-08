import duckdb

from data.db import init_schema, universe


def test_init_schema_creates_seven_tables():
    con = duckdb.connect(":memory:")
    init_schema(con)
    tables = {r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()}
    expected = {"prices", "daily_metrics", "earnings", "awards", "tiers", "positions", "personas"}
    assert expected.issubset(tables)
    assert len(expected) == 7


def test_universe_has_at_least_80():
    u = universe()
    assert len(u) >= 80
    assert {"ticker", "name", "theme"}.issubset(u[0].keys())
