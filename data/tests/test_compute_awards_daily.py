from __future__ import annotations

from datetime import date

from data.pipelines import compute_awards


class FakeConnection:
    def execute(self, sql, params=None):
        if "SELECT max(date) FROM prices" in sql:
            return self
        return self

    def fetchone(self):
        return (date(2026, 5, 8),)


def test_compute_awards_daily_does_not_fetch_prices_or_metrics(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(compute_awards, "init_schema", lambda con: calls.append("init_schema"))
    monkeypatch.setattr(compute_awards, "_ensure_positions", lambda con: calls.append("ensure_positions"))
    assert not hasattr(compute_awards, "run_incremental")
    assert not hasattr(compute_awards, "compute_metrics")
    monkeypatch.setattr(compute_awards, "run_daily_for", lambda con, d: calls.append(f"daily:{d}"))
    monkeypatch.setattr(compute_awards, "run_periodic_for", lambda con, d, period: calls.append(f"period:{period}:{d}"))
    monkeypatch.setattr(compute_awards, "run_earnings_awards", lambda con: calls.append("earnings_awards"))

    compute_awards.run_daily(FakeConnection())

    assert calls == [
        "init_schema",
        "ensure_positions",
        "daily:2026-05-08",
        "period:W:2026-05-08",
        "period:M:2026-05-08",
        "period:Q:2026-05-08",
        "period:H:2026-05-08",
        "period:Y:2026-05-08",
        "earnings_awards",
    ]
