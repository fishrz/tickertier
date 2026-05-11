#!/usr/bin/env python3
"""Generate the daily tier card PNG (1200x630, OG-ratio).

Reads web/public/data/today.json + meta.json
Writes web/public/data/cards/daily-<date>.png  and  daily-latest.png

Style: newspaper / serif headline + mono stats. Black on cream.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "web" / "public" / "data"
OUT_DIR = DATA / "cards"

WIDTH, HEIGHT = 1200, 630
PAPER = (245, 240, 228)  # cream
INK = (10, 10, 10)
GOLD = (180, 138, 50)
MUTE = (120, 116, 105)
POS = (26, 122, 58)
NEG = (170, 36, 36)

# Fonts — prefer DejaVu Serif for ticker headlines, WQY Zen Hei for CJK
SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
CJK = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"


def font(path: str, size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_winner(awards: list[dict[str, Any]], code: str) -> dict[str, Any] | None:
    for a in awards:
        if a.get("code") == code:
            ws = a.get("winners") or []
            for w in ws:
                if w.get("rank") == 1:
                    return w
            if ws:
                return ws[0]
    return None


def fmt_pct(v: Any) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "n/a"
    if abs(n) <= 1:
        n *= 100
    sign = "+" if n > 0 else ""
    return f"{sign}{n:.2f}%"


# Tier order + colors mirroring the web
TIER_ORDER = ["🔥 夯死了", "👑 顶级", "💪 人上人", "😐 NPC", "💩 拉完了", "☠️ 答辩"]
TIER_LABEL = ["夯死了", "顶级", "人上人", "NPC", "拉完了", "答辩"]
TIER_COLORS = [GOLD, (200, 165, 85), INK, MUTE, (155, 100, 60), NEG]


def render_card(today: dict[str, Any], meta: dict[str, Any]) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    d = ImageDraw.Draw(img)

    # Outer thin frame
    d.rectangle([24, 24, WIDTH - 24, HEIGHT - 24], outline=INK, width=2)

    # Top kicker
    kicker = font(MONO, 16)
    d.text((60, 56), "TICKERTIER  ·  DAILY AWARDS  ·  VOL. I", fill=INK, font=kicker)

    # Date — big serif
    date_str = today.get("date", "—")
    big = font(SERIF_BOLD, 78)
    d.text((60, 90), date_str, fill=INK, font=big)

    # Subtitle
    sub_cjk = font(CJK, 26)
    d.text((60, 184), "夯股 · 今日颁奖典礼", fill=MUTE, font=sub_cjk)

    # Divider
    d.line([(60, 232), (WIDTH - 60, 232)], fill=INK, width=1)

    awards = today.get("awards", [])
    king = find_winner(awards, "daily_king")
    clown = find_winner(awards, "daily_clown")

    # Two-column hero: king (left) / clown (right)
    col_y = 268
    col_w = (WIDTH - 120) // 2

    # Left col
    label_cjk = font(CJK, 22)
    label_mono = font(MONO, 18)
    d.text((60, col_y), "[KING]   今日股王", fill=GOLD, font=label_cjk)
    if king:
        d.text((60, col_y + 40), king.get("ticker", "—"), fill=INK, font=font(SERIF_BOLD, 100))
        d.text((60, col_y + 160), fmt_pct(king.get("metric")), fill=POS, font=font(MONO, 46))

    # Divider vertical
    d.line([(WIDTH // 2, col_y), (WIDTH // 2, col_y + 220)], fill=INK, width=1)

    # Right col
    d.text((WIDTH // 2 + 30, col_y), "[TANK]   今日答辩", fill=NEG, font=label_cjk)
    if clown:
        d.text((WIDTH // 2 + 30, col_y + 40), clown.get("ticker", "—"), fill=INK, font=font(SERIF_BOLD, 100))
        d.text((WIDTH // 2 + 30, col_y + 160), fmt_pct(clown.get("metric")), fill=NEG, font=font(MONO, 46))

    # Tier distribution bar
    bar_y = col_y + 220
    dist = today.get("tier_distribution", {}) or {}
    total = sum(dist.get(k, 0) for k in TIER_ORDER) or 1
    bar_x0, bar_x1 = 60, WIDTH - 60
    bar_w = bar_x1 - bar_x0
    bar_h = 22
    x = bar_x0
    for tier, color in zip(TIER_ORDER, TIER_COLORS):
        n = dist.get(tier, 0)
        if n <= 0:
            continue
        w = max(2, int(bar_w * n / total))
        d.rectangle([x, bar_y, x + w, bar_y + bar_h], fill=color)
        x += w
    # frame the bar
    d.rectangle([bar_x0, bar_y, bar_x1, bar_y + bar_h], outline=INK, width=1)

    # Tier counts label row
    label_y = bar_y + bar_h + 10
    label_font = font(CJK, 18)
    mono_small = font(MONO, 16)
    seg_w = bar_w / len(TIER_ORDER)
    for i, (label, _color) in enumerate(zip(TIER_LABEL, TIER_COLORS)):
        n = dist.get(TIER_ORDER[i], 0)
        cx = bar_x0 + int(seg_w * i + seg_w / 2)
        # CJK label
        l_bbox = d.textbbox((0, 0), label, font=label_font)
        d.text((cx - (l_bbox[2] - l_bbox[0]) // 2, label_y), label, fill=INK, font=label_font)
        n_str = str(n)
        n_bbox = d.textbbox((0, 0), n_str, font=mono_small)
        d.text((cx - (n_bbox[2] - n_bbox[0]) // 2, label_y + 26), n_str, fill=MUTE, font=mono_small)

    # Footer
    footer_y = HEIGHT - 40
    d.line([(60, footer_y - 10), (WIDTH - 60, footer_y - 10)], fill=INK, width=1)
    foot_mono = font(MONO, 14)
    universe = meta.get("universe", "—")
    awards_n = meta.get("awards", len(awards))
    foot_left = f"UNIVERSE {universe}  ·  AWARDS {awards_n}  ·  POWERED BY DUCKDB"
    d.text((60, footer_y), foot_left, fill=MUTE, font=foot_mono)
    right = "tickertier.vercel.app/daily"
    rb = d.textbbox((0, 0), right, font=foot_mono)
    d.text((WIDTH - 60 - (rb[2] - rb[0]), footer_y), right, fill=INK, font=foot_mono)

    return img


def main() -> int:
    today_path = DATA / "today.json"
    meta_path = DATA / "meta.json"
    if not today_path.exists() or not meta_path.exists():
        print(f"Missing data files: {today_path} / {meta_path}", file=sys.stderr)
        return 1

    today = load(today_path)
    meta = load(meta_path)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = render_card(today, meta)

    date = today.get("date", "unknown")
    out_dated = OUT_DIR / f"daily-{date}.png"
    out_latest = OUT_DIR / "daily-latest.png"
    img.save(out_dated, "PNG", optimize=True)
    img.save(out_latest, "PNG", optimize=True)
    print(f"wrote {out_dated} ({out_dated.stat().st_size} bytes)")
    print(f"wrote {out_latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
