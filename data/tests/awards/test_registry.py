"""Tests for award registry and helpers."""
from datetime import date

from data.awards._helpers import parse_period_key, period_key_for
from data.awards.registry import awards_for_period, get_award, list_awards


def test_list_awards_count():
    codes = list_awards()
    assert len(codes) == 17


def test_get_award_returns_callable():
    fn, periods, group = get_award("daily_king")
    assert callable(fn)
    assert "D" in periods
    assert group == "daily"


def test_awards_for_period_daily_has_eight():
    daily = awards_for_period("D")
    # 8 daily + 2 portfolio = 10 D-period awards
    assert len(daily) == 10


def test_period_key_for_round_trip():
    d = date(2024, 6, 5)  # Wednesday
    assert period_key_for(d, "D") == "2024-06-05"
    assert period_key_for(d, "M") == "2024-06"
    assert period_key_for(d, "Q") == "2024-Q2"
    assert period_key_for(d, "H") == "2024-H1"
    assert period_key_for(d, "Y") == "2024"
    assert period_key_for(d, "W") == "2024-W23"


def test_parse_period_key_month():
    s, e = parse_period_key("M", "2024-06")
    assert s == date(2024, 6, 1)
    assert e == date(2024, 6, 30)


def test_parse_period_key_quarter():
    s, e = parse_period_key("Q", "2024-Q2")
    assert s == date(2024, 4, 1)
    assert e == date(2024, 6, 30)


def test_parse_period_key_half():
    s, e = parse_period_key("H", "2024-H2")
    assert s == date(2024, 7, 1)
    assert e == date(2024, 12, 31)
