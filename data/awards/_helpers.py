"""Shared helpers for award computers."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable


def parse_period_key(period: str, key: str) -> tuple[date, date]:
    """Return (start, end_inclusive) trading-day range for a period_key.

    period in {D, W, M, Q, H, Y, E}.
    """
    p = period.upper()
    if p == "D":
        d = datetime.strptime(key, "%Y-%m-%d").date()
        return d, d
    if p == "W":
        # ISO: '2026-W19'
        y, w = key.split("-W")
        d = date.fromisocalendar(int(y), int(w), 1)  # Monday
        return d, d + timedelta(days=6)
    if p == "M":
        y, m = key.split("-")
        s = date(int(y), int(m), 1)
        if int(m) == 12:
            e = date(int(y), 12, 31)
        else:
            e = date(int(y), int(m) + 1, 1) - timedelta(days=1)
        return s, e
    if p == "Q":
        y, q = key.split("-Q")
        q = int(q)
        sm = (q - 1) * 3 + 1
        s = date(int(y), sm, 1)
        em = sm + 2
        if em == 12:
            e = date(int(y), 12, 31)
        else:
            e = date(int(y), em + 1, 1) - timedelta(days=1)
        return s, e
    if p == "H":
        y, h = key.split("-H")
        if int(h) == 1:
            return date(int(y), 1, 1), date(int(y), 6, 30)
        return date(int(y), 7, 1), date(int(y), 12, 31)
    if p == "Y":
        y = int(key)
        return date(y, 1, 1), date(y, 12, 31)
    if p == "E":
        d = datetime.strptime(key, "%Y-%m-%d").date()
        return d, d
    raise ValueError(f"unknown period: {period}")


def period_key_for(d: date, period: str) -> str:
    p = period.upper()
    if p == "D":
        return d.isoformat()
    if p == "W":
        iso = d.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    if p == "M":
        return f"{d.year}-{d.month:02d}"
    if p == "Q":
        return f"{d.year}-Q{(d.month - 1) // 3 + 1}"
    if p == "H":
        return f"{d.year}-H{1 if d.month <= 6 else 2}"
    if p == "Y":
        return str(d.year)
    raise ValueError(period)


def top_n_with_meta(
    rows: Iterable[tuple], meta_keys: list[str], score_idx: int = 1
) -> list[tuple[str, float, dict]]:
    """Convert SQL rows like (ticker, score, *meta) into the standard tuple form."""
    out = []
    for r in rows:
        ticker = r[0]
        score = r[score_idx]
        meta = {k: r[2 + i] for i, k in enumerate(meta_keys)}
        out.append((ticker, float(score) if score is not None else 0.0, meta))
    return out
