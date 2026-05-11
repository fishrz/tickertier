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
CARD_PATH = DATA_DIR / "cards" / "daily-latest.png"
DEFAULT_CHAT_ID = "8509167029"
APP_URL = "https://tickertier.vercel.app/daily"


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


def send_photo(token: str, chat_id: str, photo_path: Path, caption: str) -> int:
    """Send a photo with caption via multipart/form-data."""
    import mimetypes
    import secrets

    boundary = secrets.token_hex(16)
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    mime = mimetypes.guess_type(photo_path.name)[0] or "image/png"
    with photo_path.open("rb") as f:
        photo_bytes = f.read()

    parts: list[bytes] = []
    def add_field(name: str, value: str) -> None:
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(value.encode("utf-8"))
        parts.append(b"\r\n")

    add_field("chat_id", chat_id)
    add_field("caption", caption)
    add_field("parse_mode", "Markdown")

    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="photo"; filename="{photo_path.name}"\r\n'.encode()
    )
    parts.append(f"Content-Type: {mime}\r\n\r\n".encode())
    parts.append(photo_bytes)
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())

    body = b"".join(parts)
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8", errors="replace")
            print(f"Telegram photo sent: status={response.status} body={text[:200]}")
            return 0
    except urllib.error.HTTPError as exc:
        body_err = exc.read().decode("utf-8", errors="replace")
        print(f"Telegram photo failed: status={exc.code} body={body_err}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Telegram photo failed: {exc}", file=sys.stderr)
        return 1


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
        print(f"[card] {CARD_PATH} exists={CARD_PATH.exists()}")
        return 0

    # Prefer photo+caption when card is present; fall back to plain message.
    if CARD_PATH.exists():
        rc = send_photo(token, chat_id, CARD_PATH, message)
        if rc == 0:
            return 0
        print("Photo send failed — falling back to text message", file=sys.stderr)

    return send_message(token, chat_id, message)


if __name__ == "__main__":
    raise SystemExit(main())
