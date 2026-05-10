#!/usr/bin/env python3
"""Daily Telegram digest for tickertier.

Reads web/public/data/today.json + meta.json
Posts a markdown summary to Telegram chat 8509167029.

Env:
  TELEGRAM_BOT_TOKEN  required
  TELEGRAM_CHAT_ID    default 8509167029
  DRY_RUN=1           print payload, don't send
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "web" / "public" / "data"
TODAY_JSON = DATA_DIR / "today.json"
META_JSON = DATA_DIR / "meta.json"
DEFAULT_CHAT_ID = "8509167029"
APP_URL = "https://tickertier.vercel.app/"  # TODO(W2-T1): switch to /daily once page exists


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _find_award(today: dict[str, Any], code: str) -> dict[str, Any] | None:
    for award in today.get("awards", []):
        if award.get("code") == code:
            return award
    return None


def _rank_one(award: dict[str, Any] | None) -> dict[str, Any] | None:
    if not award:
        return None
    winners = award.get("winners") or []
    if not winners:
        return None
    for winner in winners:
        if winner.get("rank") == 1:
            return winner
    return winners[0]


def _format_pct(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if abs(number) <= 1:
        number *= 100
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.1f}%"


def build_message(today: dict[str, Any], meta: dict[str, Any]) -> str:
    date = today.get("date") or meta.get("data_to") or "unknown"
    lines = [f"📅 *{date} · 夯股日报*", ""]

    king = _rank_one(_find_award(today, "daily_king"))
    if king:
        lines.append(f"🏆 今日股王 *{king.get('ticker', 'N/A')}* {_format_pct(king.get('metric'))}")

    clown = _rank_one(_find_award(today, "daily_clown"))
    if clown:
        lines.append(f"💩 今日答辩 *{clown.get('ticker', 'N/A')}* {_format_pct(clown.get('metric'))}")

    if lines[-1] != "":
        lines.append("")

    universe = meta.get("universe", "n/a")
    awards = meta.get("awards", "n/a")
    if isinstance(awards, int):
        awards = f"{awards:,}"
    lines.extend(
        [
            f"📊 universe: {universe} / awards: {awards}",
            "",
            f"🌐 {APP_URL}",
        ]
    )
    return "\n".join(lines)


def send_message(token: str, chat_id: str, text: str) -> int:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    ).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"Telegram notify sent: status={response.status} body={body}")
            return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Telegram notify failed: status={exc.code} body={body}", file=sys.stderr)
        return 0
    except urllib.error.URLError as exc:
        print(f"Telegram notify failed: {exc}", file=sys.stderr)
        return 0


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", DEFAULT_CHAT_ID).strip() or DEFAULT_CHAT_ID
    dry_run = os.environ.get("DRY_RUN") == "1"

    if not token:
        print("TELEGRAM_BOT_TOKEN is required", file=sys.stderr)
        return 1

    today = _load_json(TODAY_JSON)
    meta = _load_json(META_JSON)
    message = build_message(today, meta)

    if dry_run:
        print(message)
        return 0

    return send_message(token, chat_id, message)


if __name__ == "__main__":
    raise SystemExit(main())
