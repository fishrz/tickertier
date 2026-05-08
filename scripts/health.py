"""Operational health checks for the Stock Awards daily pipeline."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date

import duckdb

from data.db import get_conn, universe


@dataclass(frozen=True)
class HealthReport:
    ok: bool
    as_of: date | None
    prices_count: int
    daily_awards_count: int
    tier_count: int
    expected_tickers: int
    issues: list[str]


def _latest_price_date(con: duckdb.DuckDBPyConnection) -> date | None:
    return con.execute("SELECT MAX(date) FROM prices").fetchone()[0]


def check_health(
    con: duckdb.DuckDBPyConnection,
    *,
    expected_tickers: int | None = None,
    as_of: date | None = None,
) -> HealthReport:
    """Validate that the latest pipeline output has price, award, and tier coverage."""
    expected = expected_tickers if expected_tickers is not None else len(universe())
    check_date = as_of or _latest_price_date(con)
    issues: list[str] = []

    if check_date is None:
        return HealthReport(
            ok=False,
            as_of=None,
            prices_count=0,
            daily_awards_count=0,
            tier_count=0,
            expected_tickers=expected,
            issues=["no prices found"],
        )

    prices_count = con.execute(
        "SELECT COUNT(DISTINCT ticker) FROM prices WHERE date = ?",
        [check_date],
    ).fetchone()[0]
    daily_awards_count = con.execute(
        "SELECT COUNT(*) FROM awards WHERE period = 'D' AND period_key = ?",
        [check_date.isoformat()],
    ).fetchone()[0]
    tier_count = con.execute(
        "SELECT COUNT(DISTINCT ticker) FROM tiers WHERE date = ?",
        [check_date],
    ).fetchone()[0]

    if prices_count < expected:
        issues.append(f"prices coverage is {prices_count}/{expected} for {check_date.isoformat()}")
    if daily_awards_count == 0:
        issues.append(f"no daily awards for {check_date.isoformat()}")
    if tier_count < expected:
        issues.append(f"tier coverage is {tier_count}/{expected} for {check_date.isoformat()}")

    return HealthReport(
        ok=not issues,
        as_of=check_date,
        prices_count=int(prices_count),
        daily_awards_count=int(daily_awards_count),
        tier_count=int(tier_count),
        expected_tickers=expected,
        issues=issues,
    )


def print_report(report: HealthReport) -> None:
    as_of = report.as_of.isoformat() if report.as_of else "n/a"
    print(f"as_of: {as_of}")
    print(f"prices: {report.prices_count}/{report.expected_tickers}")
    print(f"daily_awards: {report.daily_awards_count}")
    print(f"tiers: {report.tier_count}/{report.expected_tickers}")
    if report.ok:
        print("OK")
        return
    print("ISSUES")
    for issue in report.issues:
        print(f"- {issue}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check latest Stock Awards pipeline health.")
    parser.add_argument("--expected-tickers", type=int, default=None)
    parser.add_argument("--as-of", type=date.fromisoformat, default=None, help="YYYY-MM-DD")
    args = parser.parse_args()

    con = get_conn(read_only=True)
    try:
        report = check_health(con, expected_tickers=args.expected_tickers, as_of=args.as_of)
    finally:
        con.close()
    print_report(report)
    raise SystemExit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
