from __future__ import annotations

from datetime import date

import duckdb

from data.db import init_schema
from scripts.health import check_health


def _con(tmp_path):
    con = duckdb.connect(str(tmp_path / "health.duckdb"))
    init_schema(con)
    return con


def test_check_health_ok_for_latest_market_day(tmp_path):
    con = _con(tmp_path)
    tickers = [f"T{i:02d}" for i in range(81)]
    as_of = date(2026, 5, 8)
    con.executemany(
        "INSERT INTO prices (ticker, date, open, high, low, close, adj_close, volume) VALUES (?, ?, 1, 1, 1, 1, 1, 100)",
        [(ticker, as_of) for ticker in tickers],
    )
    con.executemany(
        "INSERT INTO tiers (ticker, date, tier, score, rank_pct) VALUES (?, ?, '😐 NPC', 0, 0.5)",
        [(ticker, as_of) for ticker in tickers],
    )
    con.execute(
        "INSERT INTO awards (award_code, period, period_key, rank, ticker, metric, meta) VALUES ('daily_mvp', 'D', ?, 1, 'T00', 1, '{}')",
        [as_of.isoformat()],
    )

    report = check_health(con, expected_tickers=81, as_of=as_of)

    assert report.ok is True
    assert report.issues == []
    assert report.as_of == as_of
    assert report.prices_count == 81
    assert report.tier_count == 81
    assert report.daily_awards_count == 1


def test_check_health_reports_missing_coverage(tmp_path):
    con = _con(tmp_path)
    as_of = date(2026, 5, 8)
    con.execute(
        "INSERT INTO prices (ticker, date, open, high, low, close, adj_close, volume) VALUES ('NVDA', ?, 1, 1, 1, 1, 1, 100)",
        [as_of],
    )

    report = check_health(con, expected_tickers=81, as_of=as_of)

    assert report.ok is False
    assert any("prices coverage is 1/81" in issue for issue in report.issues)
    assert "no daily awards for 2026-05-08" in report.issues
    assert any("tier coverage is 0/81" in issue for issue in report.issues)
