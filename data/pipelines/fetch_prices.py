"""Yahoo Finance OHLCV fetcher and DuckDB upsert.

Run as a module:
    python -m data.pipelines.fetch_prices --backfill
    python -m data.pipelines.fetch_prices --incremental
"""
from __future__ import annotations

import argparse
import logging
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from data.db import get_conn, init_schema, universe

log = logging.getLogger(__name__)

_LONG_COLS = ["ticker", "date", "open", "high", "low", "close", "adj_close", "volume"]


def _reshape(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Reshape yfinance wide multi-index df to long format."""
    if raw is None or raw.empty:
        return pd.DataFrame(columns=_LONG_COLS)

    frames = []
    # Single-ticker case: yfinance returns flat columns
    if not isinstance(raw.columns, pd.MultiIndex):
        if len(tickers) != 1:
            return pd.DataFrame(columns=_LONG_COLS)
        df = raw.copy()
        df["ticker"] = tickers[0]
        df = df.reset_index()
        frames.append(df)
    else:
        # group_by='ticker' → columns are (ticker, field)
        top_level = list({c[0] for c in raw.columns})
        for t in tickers:
            if t not in top_level:
                log.warning("yfinance returned no data for %s, skipping", t)
                continue
            sub = raw[t].copy()
            if sub.dropna(how="all").empty:
                log.warning("yfinance returned all-NaN for %s, skipping", t)
                continue
            sub["ticker"] = t
            sub = sub.reset_index()
            frames.append(sub)

    if not frames:
        return pd.DataFrame(columns=_LONG_COLS)

    df = pd.concat(frames, ignore_index=True)
    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={"adj_close": "adj_close"})
    # Ensure date column is named 'date'
    if "date" not in df.columns and "datetime" in df.columns:
        df = df.rename(columns={"datetime": "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.date
    # Make sure all expected columns exist
    for c in _LONG_COLS:
        if c not in df.columns:
            df[c] = None
    df = df[_LONG_COLS].dropna(subset=["close"])
    return df


def fetch_prices(tickers: list[str], start: date, end: date) -> pd.DataFrame:
    """Fetch OHLCV from yfinance for tickers in [start, end), return long df.

    Example:
        >>> from datetime import date
        >>> df = fetch_prices(["NVDA"], date(2024,1,2), date(2024,1,10))  # doctest: +SKIP
        >>> set(df.columns) >= {"ticker","date","close","adj_close","volume"}  # doctest: +SKIP
        True
    """
    if not tickers:
        return pd.DataFrame(columns=_LONG_COLS)
    raw = yf.download(
        tickers=tickers,
        start=start.isoformat(),
        end=end.isoformat(),
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )
    return _reshape(raw, tickers)


def upsert_prices(con, df: pd.DataFrame) -> int:
    """INSERT OR REPLACE rows into the prices table. Returns row count written.

    Example:
        >>> import duckdb
        >>> con = duckdb.connect(":memory:")
        >>> init_schema(con)
        >>> upsert_prices(con, pd.DataFrame(columns=_LONG_COLS))
        0
    """
    if df is None or df.empty:
        return 0
    con.register("_incoming", df)
    con.execute("INSERT OR REPLACE INTO prices SELECT * FROM _incoming")
    con.unregister("_incoming")
    return len(df)


def run_backfill(con, years: int = 3) -> None:
    """Fetch ~`years` years of history for the universe and upsert."""
    init_schema(con)
    end = date.today() + timedelta(days=1)
    start = end - timedelta(days=int(365 * years) + 5)
    tickers = [u["ticker"] for u in universe()]
    if "QQQ" not in tickers:
        tickers = tickers + ["QQQ"]  # benchmark, used by tank/reverse_idx/tier
    df = fetch_prices(tickers, start, end)
    n = upsert_prices(con, df)
    log.info("backfill: upserted %d rows for %d tickers", n, len(tickers))


def run_incremental(con) -> None:
    """Fetch from max(date)+1 to today and upsert."""
    init_schema(con)
    row = con.execute("SELECT max(date) FROM prices").fetchone()
    last = row[0] if row else None
    end = date.today() + timedelta(days=1)
    start = (last + timedelta(days=1)) if last else end - timedelta(days=30)
    if start >= end:
        log.info("incremental: nothing to fetch (last=%s)", last)
        return
    tickers = [u["ticker"] for u in universe()]
    if "QQQ" not in tickers:
        tickers = tickers + ["QQQ"]
    df = fetch_prices(tickers, start, end)
    n = upsert_prices(con, df)
    log.info("incremental: upserted %d rows", n)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--backfill", action="store_true")
    g.add_argument("--incremental", action="store_true")
    p.add_argument("--years", type=int, default=3)
    args = p.parse_args()
    con = get_conn()
    if args.backfill:
        run_backfill(con, years=args.years)
    else:
        run_incremental(con)
    con.close()


if __name__ == "__main__":
    main()
