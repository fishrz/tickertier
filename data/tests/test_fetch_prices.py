import os
from datetime import date
from unittest.mock import patch

import duckdb
import pandas as pd
import pytest

from data.db import init_schema
from data.pipelines.fetch_prices import _reshape, fetch_prices, upsert_prices


def _wide_fixture(tickers):
    idx = pd.DatetimeIndex(pd.date_range("2024-01-02", periods=3, freq="B"), name="Date")
    fields = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    cols = pd.MultiIndex.from_product([tickers, fields])
    data = []
    for _ in range(len(idx)):
        row = []
        for t_i, _t in enumerate(tickers):
            base = 100.0 + t_i
            row += [base, base + 1, base - 1, base + 0.5, base + 0.5, 1_000_000]
        data.append(row)
    return pd.DataFrame(data, index=idx, columns=cols)


def test_reshape_long_format_two_tickers():
    raw = _wide_fixture(["NVDA", "AMD"])
    df = _reshape(raw, ["NVDA", "AMD"])
    assert list(df.columns) == [
        "ticker", "date", "open", "high", "low", "close", "adj_close", "volume"
    ]
    assert set(df["ticker"].unique()) == {"NVDA", "AMD"}
    assert len(df) == 6


def test_reshape_skips_missing_ticker(caplog):
    raw = _wide_fixture(["NVDA"])
    df = _reshape(raw, ["NVDA", "ZZZZ_NOT_REAL"])
    assert set(df["ticker"].unique()) == {"NVDA"}


def test_fetch_prices_uses_yfinance_download():
    raw = _wide_fixture(["NVDA"])
    with patch("data.pipelines.fetch_prices.yf.download", return_value=raw) as m:
        df = fetch_prices(["NVDA"], date(2024, 1, 2), date(2024, 1, 6))
    assert m.called
    assert len(df) == 3
    assert list(df.columns)[:2] == ["ticker", "date"]


def test_upsert_prices_writes_rows():
    con = duckdb.connect(":memory:")
    init_schema(con)
    raw = _wide_fixture(["NVDA", "AMD"])
    df = _reshape(raw, ["NVDA", "AMD"])
    n = upsert_prices(con, df)
    assert n == 6
    cnt = con.execute("SELECT count(*) FROM prices").fetchone()[0]
    assert cnt == 6
    # idempotent
    n2 = upsert_prices(con, df)
    assert n2 == 6
    cnt2 = con.execute("SELECT count(*) FROM prices").fetchone()[0]
    assert cnt2 == 6


@pytest.mark.integration
@pytest.mark.skipif(not os.environ.get("INTEGRATION"), reason="set INTEGRATION=1 to run")
def test_fetch_prices_integration_nvda():
    from datetime import timedelta
    end = date.today()
    start = end - timedelta(days=400)
    df = fetch_prices(["NVDA"], start, end)
    assert len(df) > 100
