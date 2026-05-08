"""Finnhub earnings fetcher with response caching and next_day_pct join.

Strategy for report_date:
  We use `client.earnings_calendar(_from, to, symbol=ticker)` to get the actual
  *report* date (Finnhub's `company_earnings.period` is the fiscal-period-end,
  not the announcement date). When the calendar API has no entry for a quarter
  (often for periods >2 years back), we fall back to fiscal_period + 30 days.

Cache:
  Raw responses are persisted to data/cache/finnhub_<ticker>.json so reruns
  don't burn API quota.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from data.db import get_conn, init_schema, universe

log = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "cache"
RATE_LIMIT_SLEEP = 1.1  # seconds between Finnhub calls (60 req/min)


def _get_client():
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        raise RuntimeError("FINNHUB_API_KEY environment variable is not set")
    import finnhub
    return finnhub.Client(api_key=key)


def _cache_path(ticker: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"finnhub_{ticker}.json"


def _load_cache(ticker: str) -> Optional[dict]:
    p = _cache_path(ticker)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return None
    return None


def _save_cache(ticker: str, payload: dict) -> None:
    _cache_path(ticker).write_text(json.dumps(payload))


def fetch_ticker_earnings(
    client, ticker: str, sleep_fn=time.sleep, use_cache: bool = True
) -> dict:
    """Fetch earnings + calendar for one ticker, with caching and rate-limit sleeps.

    Returns:
        {"earnings": [...], "calendar": [...]}

    Example:
        >>> fetch_ticker_earnings(client, "NVDA")  # doctest: +SKIP
    """
    if use_cache:
        cached = _load_cache(ticker)
        if cached is not None:
            return cached
    earnings = client.company_earnings(ticker, limit=20) or []
    sleep_fn(RATE_LIMIT_SLEEP)
    today = date.today()
    five_yr_ago = today - timedelta(days=365 * 5 + 30)
    try:
        cal_resp = client.earnings_calendar(
            _from=five_yr_ago.isoformat(),
            to=today.isoformat(),
            symbol=ticker,
            international=False,
        ) or {}
    except Exception as e:  # pragma: no cover - network defensive
        log.warning("earnings_calendar failed for %s: %s", ticker, e)
        cal_resp = {}
    sleep_fn(RATE_LIMIT_SLEEP)
    payload = {"earnings": earnings, "calendar": cal_resp.get("earningsCalendar", [])}
    _save_cache(ticker, payload)
    return payload


def _resolve_report_date(fiscal_period: str, calendar: list[dict]) -> Optional[str]:
    """Find the announcement date in the calendar matching this fiscal period."""
    for c in calendar:
        if c.get("period") == fiscal_period and c.get("date"):
            return c["date"]
    return None


def _next_trading_close_pct(prices: pd.DataFrame, ticker: str, report_date: date) -> Optional[float]:
    """Return pct_change of the first trading day on/after report_date for ticker."""
    sub = prices[(prices["ticker"] == ticker) & (prices["date"] >= report_date)]
    if sub.empty:
        return None
    sub = sub.sort_values("date").reset_index(drop=True)
    first = sub.iloc[0]
    # find prior close
    prior = prices[(prices["ticker"] == ticker) & (prices["date"] < first["date"])]
    if prior.empty:
        return None
    prev_close = prior.sort_values("date").iloc[-1]["close"]
    if not prev_close:
        return None
    return float((first["close"] - prev_close) / prev_close)


def build_earnings_rows(payload: dict, ticker: str, prices: pd.DataFrame) -> list[dict]:
    """Convert one ticker's Finnhub payload + prices into earnings rows."""
    rows = []
    for e in payload.get("earnings", []):
        fiscal = e.get("period")
        if not fiscal:
            continue
        report_str = _resolve_report_date(fiscal, payload.get("calendar", []))
        if report_str:
            report_d = date.fromisoformat(report_str)
        else:
            # Fallback: fiscal-period + ~30 days (common report lag)
            report_d = date.fromisoformat(fiscal) + timedelta(days=30)
        next_pct = _next_trading_close_pct(prices, ticker, report_d)
        rows.append({
            "ticker": ticker,
            "report_date": report_d,
            "fiscal_period": date.fromisoformat(fiscal),
            "eps_actual": e.get("actual"),
            "eps_est": e.get("estimate"),
            "surprise": e.get("surprise"),
            "surprise_pct": e.get("surprisePercent"),
            "next_day_pct": next_pct,
        })
    return rows


def upsert_earnings(con, rows: list[dict]) -> int:
    """INSERT OR REPLACE earnings rows. Returns count written."""
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["ticker", "report_date"], keep="last")
    con.register("_e", df)
    con.execute("INSERT OR REPLACE INTO earnings SELECT * FROM _e")
    con.unregister("_e")
    return len(df)


def run(con=None, sleep_fn=time.sleep) -> int:
    """End-to-end: fetch earnings for the whole universe and upsert."""
    if con is None:
        con = get_conn()
    init_schema(con)
    client = _get_client()
    prices = con.execute(
        "SELECT ticker, date, close FROM prices"
    ).fetch_df()
    if not prices.empty:
        prices["date"] = pd.to_datetime(prices["date"]).dt.date
    total = 0
    for u in universe():
        t = u["ticker"]
        try:
            payload = fetch_ticker_earnings(client, t, sleep_fn=sleep_fn)
        except Exception as e:
            log.warning("skip %s: %s", t, e)
            continue
        rows = build_earnings_rows(payload, t, prices)
        total += upsert_earnings(con, rows)
    log.info("earnings: upserted %d rows", total)
    return total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
