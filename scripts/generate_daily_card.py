#!/usr/bin/env python3
"""Generate the daily tier card PNG — newspaper-style header + full tier list.

Reads: web/public/data/today.json, meta.json, tiers.json
Writes: web/public/data/cards/daily-<date>.png + daily-latest.png

Layout (1200 x ~1500):
  Header band: date + king/clown hero + universe/awards meta
  Tier table:  6 rows, color band + label + count + ticker chips
  Footer:      url + powered-by
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

WIDTH = 1200
# Height computed dynamically below

PAPER = (245, 240, 228)
INK = (10, 10, 10)
GOLD = (180, 138, 50)
MUTE = (120, 116, 105)
POS = (26, 122, 58)
NEG = (170, 36, 36)

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONO_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
CJK = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"


# Tier order (best -> worst), Chinese-only labels (emoji removed to avoid tofu)
# (key in tier_distribution / tiers.json, short label, band color, text-on-band color)
TIERS = [
    ("🔥 夯死了", "夯死了",  (227, 173, 36),  (10, 10, 10)),   # gold
    ("👑 顶级",   "顶级",    (205, 188, 130), (10, 10, 10)),   # pale gold
    ("💪 人上人", "人上人",  (45, 45, 45),   (245, 240, 228)), # ink
    ("😐 NPC",    "NPC",     (170, 165, 150), (10, 10, 10)),   # warm grey
    ("💩 拉完了", "拉完了",  (148, 92, 50),  (245, 240, 228)), # brown
    ("☠️ 答辩",   "答辩",    (155, 35, 35),  (245, 240, 228)), # red
]


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


def group_tickers(tiers_list: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Return {tier_key: [tickers sorted by score desc]}."""
    by: dict[str, list[tuple[str, float]]] = {}
    for entry in tiers_list:
        tier = entry.get("tier")
        if not tier:
            continue
        by.setdefault(tier, []).append(
            (entry.get("ticker", "—"), float(entry.get("score") or 0.0))
        )
    out: dict[str, list[str]] = {}
    for tier, items in by.items():
        items.sort(key=lambda x: -x[1])
        out[tier] = [t for t, _ in items]
    return out


# Header constants
HEADER_TOP = 0
HEADER_HEIGHT = 480   # date + king/clown + meta
LEFT_BAND_W = 220     # tier label column width
ROW_PAD_Y = 14
CHIP_PAD_X = 14
CHIP_PAD_Y = 7
CHIP_SPACING_X = 8
CHIP_SPACING_Y = 8
MOVERS_HEIGHT = 90
FOOTER_HEIGHT = 80
SIDE_PAD = 40


def measure_chip(d: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = d.textbbox((0, 0), text, font=fnt)
    # Use font's metric-based height so chips are uniform regardless of glyph
    try:
        asc, desc = fnt.getmetrics()
        h = asc + desc
    except Exception:
        h = bbox[3] - bbox[1]
    return (bbox[2] - bbox[0] + CHIP_PAD_X * 2, h + CHIP_PAD_Y * 2)


def compute_row_height(
    d: ImageDraw.ImageDraw,
    tickers: list[str],
    chip_fnt: ImageFont.ImageFont,
    content_w: int,
) -> tuple[int, list[list[tuple[str, int, int]]]]:
    """Return (row_height, rows-of-chips). Each chip = (text, w, h)."""
    rows: list[list[tuple[str, int, int]]] = []
    cur: list[tuple[str, int, int]] = []
    cur_w = 0
    for t in tickers:
        w, h = measure_chip(d, t, chip_fnt)
        # +spacing between chips
        add_w = w + (CHIP_SPACING_X if cur else 0)
        if cur and cur_w + add_w > content_w:
            rows.append(cur)
            cur = [(t, w, h)]
            cur_w = w
        else:
            cur.append((t, w, h))
            cur_w += add_w
    if cur:
        rows.append(cur)
    if not rows:
        rows = [[]]
    chip_h = rows[0][0][2] if rows[0] else 36
    row_h = ROW_PAD_Y * 2 + len(rows) * chip_h + (len(rows) - 1) * CHIP_SPACING_Y
    return row_h, rows


def render_movers(d: ImageDraw.ImageDraw, today: dict[str, Any], y: int) -> None:
    """Render the tier movers strip: top upgrade(s) ↑ and top downgrade(s) ↓."""
    movers = today.get("tier_movers") or []
    if not movers:
        return
    ups = [m for m in movers if m.get("delta", 0) > 0][:3]
    downs = [m for m in movers if m.get("delta", 0) < 0][-3:]

    kicker = font(MONO, 13)
    d.text(
        (SIDE_PAD + 20, y + 14),
        "TIER MOVERS  ·  今日升降一览",
        fill=MUTE,
        font=kicker,
    )

    label_fnt = font(CJK, 18)
    body_fnt = font(MONO, 22)

    line_y = y + 42
    # Left column: upgrades
    if ups:
        d.text((SIDE_PAD + 20, line_y), "↑ 升级", fill=POS, font=label_fnt)
        parts = [f"{m['ticker']} (+{m['delta']})" for m in ups]
        d.text((SIDE_PAD + 110, line_y), "  ".join(parts), fill=INK, font=body_fnt)
    # Right column: downgrades
    if downs:
        right_text_parts = [f"{m['ticker']} ({m['delta']})" for m in downs]
        right_text = "  ".join(right_text_parts)
        tb = d.textbbox((0, 0), right_text, font=body_fnt)
        text_w = tb[2] - tb[0]
        right_x = WIDTH - SIDE_PAD - 20 - text_w
        label = "↓ 降级"
        lb = d.textbbox((0, 0), label, font=label_fnt)
        label_w = lb[2] - lb[0]
        d.text((right_x - label_w - 16, line_y), label, fill=NEG, font=label_fnt)
        d.text((right_x, line_y), right_text, fill=INK, font=body_fnt)

    # Separator line under the band
    d.line(
        [(SIDE_PAD, y + MOVERS_HEIGHT - 1), (WIDTH - SIDE_PAD, y + MOVERS_HEIGHT - 1)],
        fill=INK,
        width=1,
    )


def render_header(d: ImageDraw.ImageDraw, today: dict[str, Any], meta: dict[str, Any]) -> None:
    # Outer kicker
    kicker = font(MONO, 16)
    d.text((SIDE_PAD + 20, 56), "TICKERTIER  ·  DAILY TIER LIST  ·  VOL. I", fill=INK, font=kicker)

    # Date
    big = font(SERIF_BOLD, 78)
    d.text((SIDE_PAD + 20, 86), today.get("date", "—"), fill=INK, font=big)

    # Subtitle
    sub_cjk = font(CJK, 24)
    d.text((SIDE_PAD + 20, 178), "夯股 · 今日颁奖典礼", fill=MUTE, font=sub_cjk)

    # Divider
    d.line([(SIDE_PAD + 20, 220), (WIDTH - SIDE_PAD - 20, 220)], fill=INK, width=1)

    awards = today.get("awards", [])
    king = find_winner(awards, "daily_king")
    clown = find_winner(awards, "daily_clown")

    col_y = 244
    # Left col
    label_cjk = font(CJK, 22)
    d.text((SIDE_PAD + 20, col_y), "[KING]   今日股王", fill=GOLD, font=label_cjk)
    if king:
        d.text((SIDE_PAD + 20, col_y + 36), king.get("ticker", "—"), fill=INK, font=font(SERIF_BOLD, 92))
        d.text((SIDE_PAD + 20, col_y + 142), fmt_pct(king.get("metric")), fill=POS, font=font(MONO, 40))

    # Vertical divider
    d.line([(WIDTH // 2, col_y), (WIDTH // 2, col_y + 196)], fill=INK, width=1)

    # Right col
    d.text((WIDTH // 2 + 30, col_y), "[TANK]   今日答辩", fill=NEG, font=label_cjk)
    if clown:
        d.text((WIDTH // 2 + 30, col_y + 36), clown.get("ticker", "—"), fill=INK, font=font(SERIF_BOLD, 92))
        d.text((WIDTH // 2 + 30, col_y + 142), fmt_pct(clown.get("metric")), fill=NEG, font=font(MONO, 40))

    # Meta strip
    meta_y = col_y + 210
    meta_mono = font(MONO, 16)
    universe = meta.get("universe", "—")
    awards_n = meta.get("awards", len(awards))
    if isinstance(awards_n, int):
        awards_str = f"{awards_n:,}"
    else:
        awards_str = str(awards_n)
    d.line([(SIDE_PAD + 20, meta_y - 8), (WIDTH - SIDE_PAD - 20, meta_y - 8)], fill=INK, width=1)
    d.text((SIDE_PAD + 20, meta_y), f"UNIVERSE  {universe}", fill=INK, font=meta_mono)
    d.text((SIDE_PAD + 220, meta_y), f"AWARDS  {awards_str}", fill=INK, font=meta_mono)
    d.text((SIDE_PAD + 460, meta_y), "FULL TIER LIST  ▼", fill=MUTE, font=meta_mono)


def render_card(today: dict[str, Any], meta: dict[str, Any], tiers_list: list[dict[str, Any]]) -> Image.Image:
    grouped = group_tickers(tiers_list)
    dist = today.get("tier_distribution", {}) or {}

    # Decide row heights given fixed chip font
    # Use a throwaway draw to measure
    tmp = Image.new("RGB", (10, 10), PAPER)
    td = ImageDraw.Draw(tmp)
    chip_fnt = font(MONO, 22)
    content_w = WIDTH - 2 * SIDE_PAD - LEFT_BAND_W - 20

    layouts = []
    total_table_h = 0
    for key, _short, _band, _txt in TIERS:
        tickers = grouped.get(key, [])
        # Fallback: synthesize from count if list missing
        if not tickers:
            n = dist.get(key, 0)
            tickers = ["—"] * (n if n and n < 99 else 0)
        row_h, rows = compute_row_height(td, tickers, chip_fnt, content_w)
        # Min row height for label clarity
        row_h = max(row_h, 96)
        layouts.append((key, tickers, row_h, rows))
        total_table_h += row_h

    height = HEADER_HEIGHT + total_table_h + MOVERS_HEIGHT + FOOTER_HEIGHT
    img = Image.new("RGB", (WIDTH, height), PAPER)
    d = ImageDraw.Draw(img)

    # Outer frame
    d.rectangle([24, 24, WIDTH - 24, height - 24], outline=INK, width=2)

    # Header
    render_header(d, today, meta)

    # Tier table
    y = HEADER_HEIGHT
    band_x0 = SIDE_PAD
    band_x1 = SIDE_PAD + LEFT_BAND_W
    chips_x0 = band_x1 + 20
    chips_x1 = WIDTH - SIDE_PAD

    for idx, ((key, short, band_color, text_on_band), tickers, row_h, rows) in enumerate(zip(TIERS, [l[1] for l in layouts], [l[2] for l in layouts], [l[3] for l in layouts])):
        # Background tint for the whole row (very light)
        tint = tuple(int(PAPER[i] * 0.55 + band_color[i] * 0.45) for i in range(3))
        d.rectangle([SIDE_PAD, y, WIDTH - SIDE_PAD, y + row_h], fill=PAPER)

        # Color band on the left
        d.rectangle([band_x0, y, band_x1, y + row_h], fill=band_color)
        # Tier label (CJK) centered in band
        label_fnt = font(CJK, 34)
        lbbox = d.textbbox((0, 0), short, font=label_fnt)
        lw = lbbox[2] - lbbox[0]
        lh = lbbox[3] - lbbox[1]
        d.text(
            (band_x0 + (LEFT_BAND_W - lw) // 2, y + row_h // 2 - lh - 6),
            short,
            fill=text_on_band,
            font=label_fnt,
        )
        # Count below
        n = dist.get(key, len(tickers))
        count_fnt = font(MONO, 20)
        cbbox = d.textbbox((0, 0), f"× {n}", font=count_fnt)
        cw = cbbox[2] - cbbox[0]
        d.text(
            (band_x0 + (LEFT_BAND_W - cw) // 2, y + row_h // 2 + 6),
            f"× {n}",
            fill=text_on_band,
            font=count_fnt,
        )

        # Chips
        cy = y + ROW_PAD_Y
        for row in rows:
            cx = chips_x0
            for text, w, h in row:
                # Chip background
                d.rounded_rectangle(
                    [cx, cy, cx + w, cy + h],
                    radius=4,
                    fill=PAPER,
                    outline=INK,
                    width=1,
                )
                # Text — center on actual glyph bbox (caps-only tickers)
                tb = d.textbbox((0, 0), text, font=chip_fnt)
                glyph_w = tb[2] - tb[0]
                glyph_h = tb[3] - tb[1]
                text_x = cx + (w - glyph_w) // 2 - tb[0]
                text_y = cy + (h - glyph_h) // 2 - tb[1]
                d.text((text_x, text_y), text, fill=INK, font=chip_fnt)
                cx += w + CHIP_SPACING_X
            cy += (row[0][2] if row else 36) + CHIP_SPACING_Y

        # Row separator
        d.line([(SIDE_PAD, y + row_h), (WIDTH - SIDE_PAD, y + row_h)], fill=INK, width=1)
        y += row_h

    # Movers band
    movers_y = y
    render_movers(d, today, movers_y)

    # Footer
    foot_y = height - FOOTER_HEIGHT + 24
    foot_mono = font(MONO, 14)
    d.text(
        (SIDE_PAD + 20, foot_y),
        "POWERED BY DUCKDB · YFINANCE · 个人娱乐用 · 不构成投资建议",
        fill=MUTE,
        font=foot_mono,
    )
    right = "tickertier.vercel.app/daily"
    rb = d.textbbox((0, 0), right, font=foot_mono)
    d.text(
        (WIDTH - SIDE_PAD - 20 - (rb[2] - rb[0]), foot_y),
        right,
        fill=INK,
        font=foot_mono,
    )

    return img


def main() -> int:
    today_path = DATA / "today.json"
    meta_path = DATA / "meta.json"
    tiers_path = DATA / "tiers.json"
    for p in (today_path, meta_path, tiers_path):
        if not p.exists():
            print(f"Missing data file: {p}", file=sys.stderr)
            return 1

    today = load(today_path)
    meta = load(meta_path)
    tiers_doc = load(tiers_path)
    tiers_list = tiers_doc.get("tiers") or tiers_doc.get("members") or []
    # Old shape compat: dict of tier -> list[ticker]
    if isinstance(tiers_list, dict):
        flat = []
        for tier, items in tiers_list.items():
            for t in items:
                flat.append({"tier": tier, "ticker": t, "score": 0.0})
        tiers_list = flat

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = render_card(today, meta, tiers_list)

    date = today.get("date", "unknown")
    out_dated = OUT_DIR / f"daily-{date}.png"
    out_latest = OUT_DIR / "daily-latest.png"
    img.save(out_dated, "PNG", optimize=True)
    img.save(out_latest, "PNG", optimize=True)
    print(f"wrote {out_dated} ({out_dated.stat().st_size} bytes, {img.size[0]}x{img.size[1]})")
    print(f"wrote {out_latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
