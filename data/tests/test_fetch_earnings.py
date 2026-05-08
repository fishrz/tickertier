from datetime import date
from unittest.mock import MagicMock

import duckdb
import pandas as pd
import pytest

from data.db import init_schema
from data.pipelines import fetch_earnings as fe


@pytest.fixture
def fake_prices():
    rows = [
        ("NVDA", date(2024, 2, 20), 700.0),
        ("NVDA", date(2024, 2, 21), 700.0),  # report day (after-hours)
        ("NVDA", date(2024, 2, 22), 770.0),  # next trading day -> +10%
        ("NVDA", date(2024, 2, 23), 760.0),
    ]
    return pd.DataFrame(rows, columns=["ticker", "date", "close"])


def test_resolve_report_date_uses_calendar():
    cal = [{"period": "2024-01-31", "date": "2024-02-21"}]
    assert fe._resolve_report_date("2024-01-31", cal) == "2024-02-21"
    assert fe._resolve_report_date("2099-01-01", cal) is None


def test_next_trading_close_pct_picks_first_day_on_or_after(fake_prices):
    pct = fe._next_trading_close_pct(fake_prices, "NVDA", date(2024, 2, 22))
    assert pct == pytest.approx((770.0 - 700.0) / 700.0)


def test_next_trading_close_pct_handles_weekend_report(fake_prices):
    # Reported Saturday 2024-02-24 -> no trading day on/after in fixture
    assert fe._next_trading_close_pct(fake_prices, "NVDA", date(2024, 2, 24)) is None


def test_build_earnings_rows_uses_calendar_when_present(fake_prices):
    payload = {
        "earnings": [{
            "period": "2024-01-31",
            "actual": 5.16, "estimate": 4.64,
            "surprise": 0.52, "surprisePercent": 11.2,
        }],
        "calendar": [{"period": "2024-01-31", "date": "2024-02-22"}],
    }
    rows = fe.build_earnings_rows(payload, "NVDA", fake_prices)
    assert len(rows) == 1
    r = rows[0]
    assert r["ticker"] == "NVDA"
    assert r["report_date"] == date(2024, 2, 22)
    assert r["fiscal_period"] == date(2024, 1, 31)
    assert r["next_day_pct"] == pytest.approx((770.0 - 700.0) / 700.0)
    assert r["eps_actual"] == 5.16


def test_build_earnings_rows_fallback_when_calendar_missing(fake_prices):
    payload = {
        "earnings": [{"period": "2024-01-31", "actual": 1, "estimate": 1,
                      "surprise": 0, "surprisePercent": 0}],
        "calendar": [],
    }
    rows = fe.build_earnings_rows(payload, "NVDA", fake_prices)
    # fallback = fiscal + 30 days = 2024-03-01 → no price on/after in fixture
    assert rows[0]["report_date"] == date(2024, 3, 1)
    assert rows[0]["next_day_pct"] is None


def test_fetch_ticker_earnings_calls_sleep_between_requests(tmp_path, monkeypatch):
    monkeypatch.setattr(fe, "CACHE_DIR", tmp_path)
    sleeps = []
    client = MagicMock()
    client.company_earnings.return_value = [{"period": "2024-01-31"}]
    client.earnings_calendar.return_value = {"earningsCalendar": []}
    payload = fe.fetch_ticker_earnings(client, "NVDA", sleep_fn=sleeps.append, use_cache=False)
    assert client.company_earnings.called
    assert client.earnings_calendar.called
    # Sleep called after each Finnhub API call
    assert len(sleeps) == 2
    assert all(s == pytest.approx(fe.RATE_LIMIT_SLEEP) for s in sleeps)
    # Cached to disk
    assert (tmp_path / "finnhub_NVDA.json").exists()
    assert payload["earnings"][0]["period"] == "2024-01-31"


def test_fetch_ticker_earnings_uses_cache_when_present(tmp_path, monkeypatch):
    monkeypatch.setattr(fe, "CACHE_DIR", tmp_path)
    (tmp_path / "finnhub_NVDA.json").write_text(
        '{"earnings":[{"period":"2024-01-31"}],"calendar":[]}'
    )
    client = MagicMock()
    payload = fe.fetch_ticker_earnings(client, "NVDA", sleep_fn=lambda s: None)
    assert not client.company_earnings.called
    assert payload["earnings"][0]["period"] == "2024-01-31"


def test_upsert_earnings_writes_rows():
    con = duckdb.connect(":memory:")
    init_schema(con)
    rows = [{
        "ticker": "NVDA",
        "report_date": date(2024, 2, 22),
        "fiscal_period": date(2024, 1, 31),
        "eps_actual": 5.16, "eps_est": 4.64,
        "surprise": 0.52, "surprise_pct": 11.2,
        "next_day_pct": 0.10,
    }]
    n = fe.upsert_earnings(con, rows)
    assert n == 1
    cnt = con.execute("SELECT count(*) FROM earnings").fetchone()[0]
    assert cnt == 1


def test_get_client_raises_without_key(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        fe._get_client()


def test_main_skip_missing_key_exits_successfully(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    monkeypatch.setattr(fe, "run", lambda: (_ for _ in ()).throw(RuntimeError("should not run")))

    with pytest.raises(SystemExit) as exc:
        fe.main(["--skip-missing-key"])

    assert exc.value.code == 0
