"""Tests for the 8 daily awards."""
from data.awards.daily import (
    daily_king, daily_clown, roller_coaster, oscar, comeback,
    npc_god, pump_army, tank,
)

DATE = "2024-06-03"


def test_daily_king(con_metrics):
    res = daily_king.compute(con_metrics, DATE)
    assert res[0][0] == "AAA"
    assert res[0][1] > 0


def test_daily_clown(con_metrics):
    res = daily_clown.compute(con_metrics, DATE)
    assert res[0][0] == "BBB"
    assert res[0][1] < 0


def test_roller_coaster(con_metrics):
    res = roller_coaster.compute(con_metrics, DATE)
    assert res[0][0] == "CCC"


def test_oscar_filters_gap_positive(con_metrics):
    res = oscar.compute(con_metrics, DATE)
    tickers = [r[0] for r in res]
    # CCC had gap < 0, FFF had gap < 0 → excluded.
    assert "CCC" not in tickers
    assert "FFF" not in tickers
    # BBB had gap=0.03 with fade -0.10 → biggest fade among positive-gap rows
    assert res[0][0] == "BBB"


def test_comeback_requires_positive_pct(con_metrics):
    res = comeback.compute(con_metrics, DATE)
    tickers = [r[0] for r in res]
    assert "BBB" not in tickers and "GGG" not in tickers
    # CCC and FFF both have rebound=0.20 / 0.10 → CCC wins
    assert res[0][0] == "CCC"


def test_npc_god(con_metrics):
    res = npc_god.compute(con_metrics, DATE)
    # Only DDD (vol_ratio=0.5) and GGG (vol_ratio=0.6) qualify
    tickers = [r[0] for r in res]
    assert tickers[0] == "DDD"
    assert "AAA" not in tickers


def test_pump_army(con_metrics):
    res = pump_army.compute(con_metrics, DATE)
    # Positive pct, sorted by vol_ratio desc → CCC (3.0) first
    assert res[0][0] == "CCC"
    tickers = [r[0] for r in res]
    assert "BBB" not in tickers  # negative pct excluded


def test_tank_qqq_down(con_metrics):
    # QQQ pct = -1.2% < -0.5% threshold → tank fires
    res = tank.compute(con_metrics, DATE)
    assert len(res) > 0
    tickers = [r[0] for r in res]
    assert "QQQ" not in tickers
    assert res[0][0] == "AAA"  # best performer that day


def test_tank_skips_when_qqq_up(con_metrics):
    con_metrics.execute(
        "UPDATE daily_metrics SET pct_change = 0.01 WHERE ticker='QQQ' AND date=?",
        [DATE],
    )
    res = tank.compute(con_metrics, DATE)
    assert res == []


def test_tank_skips_when_qqq_missing(con_metrics):
    con_metrics.execute("DELETE FROM daily_metrics WHERE ticker='QQQ' AND date=?", [DATE])
    res = tank.compute(con_metrics, DATE)
    assert res == []
