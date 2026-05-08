from datetime import date

import duckdb
import pandas as pd
import pytest

from data.db import init_schema
from data.pipelines.compute_metrics import compute_metrics


@pytest.fixture
def con_with_prices():
    con = duckdb.connect(":memory:")
    init_schema(con)
    rows = []
    # NVDA: 5 days
    nvda = [
        # date, open, high, low, close, adj_close, volume
        (date(2024, 1, 2), 100, 105, 99, 102, 102, 1_000_000),
        (date(2024, 1, 3), 102, 110, 101, 108, 108, 2_000_000),
        (date(2024, 1, 4), 108, 112, 107, 110, 110, 1_500_000),
        (date(2024, 1, 5), 110, 113, 105, 106, 106, 3_000_000),
        (date(2024, 1, 8), 106, 108, 104, 107, 107, 1_200_000),
    ]
    for d, o, h, low_, c, ac, v in nvda:
        rows.append(("NVDA", d, o, h, low_, c, ac, v))
    amd = [
        (date(2024, 1, 2), 50, 52, 49, 51, 51, 500_000),
        (date(2024, 1, 3), 51, 53, 50, 52, 52, 600_000),
        (date(2024, 1, 4), 52, 55, 51, 54, 54, 700_000),
        (date(2024, 1, 5), 54, 56, 53, 55, 55, 800_000),
        (date(2024, 1, 8), 55, 57, 54, 56, 56, 900_000),
    ]
    for d, o, h, low_, c, ac, v in amd:
        rows.append(("AMD", d, o, h, low_, c, ac, v))
    df = pd.DataFrame(rows, columns=[
        "ticker", "date", "open", "high", "low", "close", "adj_close", "volume"
    ])
    con.register("_p", df)
    con.execute("INSERT INTO prices SELECT * FROM _p")
    con.unregister("_p")
    return con


def test_compute_metrics_rowcount(con_with_prices):
    n = compute_metrics(con_with_prices)
    assert n == 10  # 2 tickers * 5 days


def test_compute_metrics_pct_change_known_row(con_with_prices):
    compute_metrics(con_with_prices)
    # NVDA 2024-01-03: (108-102)/102
    row = con_with_prices.execute(
        "SELECT pct_change, intraday_amp, gap, rebound, fade FROM daily_metrics "
        "WHERE ticker='NVDA' AND date='2024-01-03'"
    ).fetchone()
    assert row[0] == pytest.approx((108 - 102) / 102)
    assert row[1] == pytest.approx((110 - 101) / 102)  # intraday_amp
    assert row[2] == pytest.approx((102 - 102) / 102)  # gap
    assert row[3] == pytest.approx((108 - 101) / 101)  # rebound
    assert row[4] == pytest.approx((108 - 110) / 110)  # fade


def test_compute_metrics_first_row_pct_change_null(con_with_prices):
    compute_metrics(con_with_prices)
    row = con_with_prices.execute(
        "SELECT pct_change FROM daily_metrics WHERE ticker='NVDA' AND date='2024-01-02'"
    ).fetchone()
    assert row[0] is None


def test_compute_metrics_std5_and_vol_ratio(con_with_prices):
    compute_metrics(con_with_prices)
    # std_5 on day 5 for NVDA = stddev of [102,108,110,106,107]
    row = con_with_prices.execute(
        "SELECT std_5, vol_ratio_20 FROM daily_metrics "
        "WHERE ticker='NVDA' AND date='2024-01-08'"
    ).fetchone()
    import statistics
    expected = statistics.stdev([102, 108, 110, 106, 107])
    assert row[0] == pytest.approx(expected, rel=1e-6)
    # vol_ratio_20 = 1.2M / mean of all 5 vols (since <20 prior)
    avg_vol = sum([1_000_000, 2_000_000, 1_500_000, 3_000_000, 1_200_000]) / 5
    assert row[1] == pytest.approx(1_200_000 / avg_vol)
