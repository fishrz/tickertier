#!/usr/bin/env python3
"""Generate per-ticker OG share images.

Reads:  web/public/data/stocks.json (+ today.json for current tier)
Writes: web/public/og/stock-<TICKER>.png  (1200x630)

Layout (newspaper-style, single hero):
  TOP    : kicker (TICKERTIER · STOCK)
  LEFT   : huge TICKER + 中文名 + 板块/persona + 当前 tier badge
  RIGHT  : last close + pct change (color) + 累计奖牌 + 最佳奖 + streak chips
  FOOTER : URL + powered-by
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "web" / "public" / "data"
OUT_DIR = ROOT / "web" / "public" / "og"

W, H = 1200, 630
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
CJK = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

# Tier color hint for left badge
TIER_BG = {
    "🔥 夯死了": ((227, 173, 36), (10, 10, 10)),
    "👑 顶级":   ((205, 188, 130), (10, 10, 10)),
    "💪 人上人": ((45, 45, 45), (245, 240, 228)),
    "😐 NPC":    ((170, 165, 150), (10, 10, 10)),
    "💩 拉完了": ((148, 92, 50), (245, 240, 228)),
    "☠️ 答辩":   ((155, 35, 35), (245, 240, 228)),
}


def fnt(p: str, sz: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype(p, sz)
    except OSError:
        return ImageFont.load_default()


def short_tier(label: str) -> str:
    # Strip leading emoji + space (PIL can't render colour emoji cleanly)
    parts = label.split(" ", 1)
    return parts[1] if len(parts) == 2 else label


def fmt_pct(v: Any) -> str:
    try:
        x = float(v)
        # stocks.json stores pct_change as a fraction (e.g. 0.2658 = 26.58%)
        if -1.5 < x < 1.5:
            x *= 100
        return f"{x:+.2f}%"
    except Exception:
        return "—"


def render(stock: dict, today_tier: str | None) -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # Outer frame
    d.rectangle([20, 20, W - 20, H - 20], outline=INK, width=2)

    # Kicker
    d.text((50, 44), "TICKERTIER  ·  STOCK SPOTLIGHT", fill=INK, font=fnt(MONO, 16))
    d.line([(50, 78), (W - 50, 78)], fill=INK, width=1)

    ticker = stock.get("ticker", "—")
    name = stock.get("name", "")
    theme = stock.get("theme") or ""
    persona = stock.get("persona") or ""
    last_close = stock.get("last_close") or stock.get("close")
    last_pct = stock.get("last_pct_change")
    if last_pct is None:
        last_pct = stock.get("pct_change")
    medal_count = stock.get("medal_count") or {}
    total_medals = 0
    if isinstance(medal_count, dict) and medal_count:
        total_medals = sum(medal_count.values())
    else:
        # Fall back to summing medal_history counts
        mh_tmp = stock.get("medal_history") or []
        total_medals = sum(int(m.get("count") or 0) for m in mh_tmp if isinstance(m, dict))
        if total_medals == 0:
            total_medals = int(stock.get("awards_count") or 0)
    best_award = ""
    mh = stock.get("medal_history") or []
    if mh and isinstance(mh, list):
        raw_name = mh[0].get("name") or mh[0].get("code") or ""
        # Strip leading emoji + space (PIL CJK font can't render colour emoji)
        # Heuristic: drop the first whitespace-separated token if it contains any non-ASCII non-CJK char
        if " " in raw_name:
            head, tail = raw_name.split(" ", 1)
            # If head is mostly non-letter chars (likely emoji), use tail
            if not any("\u4e00" <= c <= "\u9fff" for c in head):
                raw_name = tail
        best_award = raw_name
    streak_top = int(stock.get("streak_top_tier_days") or 0)
    streak_aw = int(stock.get("streak_in_awards_days") or 0)

    # LEFT column: ticker + name
    d.text((50, 110), ticker, fill=INK, font=fnt(SERIF_BOLD, 180))

    name_y = 310
    if name and name != ticker:
        d.text((50, name_y), name[:22], fill=INK, font=fnt(CJK, 40))
        name_y += 60

    meta_parts = []
    if theme:
        meta_parts.append(theme.upper())
    if persona:
        meta_parts.append(persona)
    if meta_parts:
        d.text((50, name_y), "  ·  ".join(meta_parts), fill=MUTE, font=fnt(CJK, 22))
        name_y += 40

    # Tier badge (today)
    if today_tier and today_tier in TIER_BG:
        bg, txt = TIER_BG[today_tier]
        label = short_tier(today_tier)
        badge_font = fnt(CJK, 26)
        bb = d.textbbox((0, 0), label, font=badge_font)
        bw = (bb[2] - bb[0]) + 36
        bh = (bb[3] - bb[1]) + 18
        bx, by = 50, name_y + 8
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=6, fill=bg)
        d.text(
            (bx + 18 - bb[0], by + 9 - bb[1]),
            label,
            fill=txt,
            font=badge_font,
        )

    # RIGHT column: price + medals
    rx = 720
    if last_close is not None:
        d.text((rx, 110), f"${last_close:.2f}", fill=INK, font=fnt(MONO, 56))
    if last_pct is not None:
        try:
            v = float(last_pct)
            color = POS if v > 0 else NEG if v < 0 else INK
            d.text((rx, 180), fmt_pct(v), fill=color, font=fnt(MONO, 44))
        except Exception:
            pass

    # Medals total
    d.text((rx, 260), str(total_medals), fill=INK, font=fnt(SERIF_BOLD, 92))
    d.text((rx, 360), "枚累计奖牌", fill=MUTE, font=fnt(CJK, 22))

    if best_award:
        d.text((rx, 400), f"最佳：{best_award[:10]}", fill=GOLD, font=fnt(CJK, 22))

    # Streak chips (bottom of right col)
    chip_y = 450
    cx = rx
    if streak_top > 1:
        label = f"连续 {streak_top} 日 顶级+"
        bf = fnt(CJK, 20)
        bb = d.textbbox((0, 0), label, font=bf)
        cw = (bb[2] - bb[0]) + 28
        ch = (bb[3] - bb[1]) + 14
        d.rounded_rectangle([cx, chip_y, cx + cw, chip_y + ch], radius=4, outline=GOLD, width=2)
        d.text((cx + 14 - bb[0], chip_y + 7 - bb[1]), label, fill=GOLD, font=bf)
        cx += cw + 12
    if streak_aw > 1:
        label = f"连续 {streak_aw} 日 摘金"
        bf = fnt(CJK, 20)
        bb = d.textbbox((0, 0), label, font=bf)
        cw = (bb[2] - bb[0]) + 28
        ch = (bb[3] - bb[1]) + 14
        d.rounded_rectangle([cx, chip_y, cx + cw, chip_y + ch], radius=4, outline=INK, width=2)
        d.text((cx + 14 - bb[0], chip_y + 7 - bb[1]), label, fill=INK, font=bf)

    # Footer
    d.line([(50, H - 70), (W - 50, H - 70)], fill=INK, width=1)
    d.text(
        (50, H - 52),
        "POWERED BY DUCKDB · YFINANCE · 个人娱乐用 · 不构成投资建议",
        fill=MUTE,
        font=fnt(CJK, 14),
    )
    right = f"tickertier.vercel.app/stock/{ticker}"
    rb_font = fnt(MONO, 14)
    rb = d.textbbox((0, 0), right, font=rb_font)
    d.text((W - 50 - (rb[2] - rb[0]), H - 52), right, fill=INK, font=rb_font)

    return img


def main() -> int:
    stocks_p = DATA / "stocks.json"
    today_p = DATA / "today.json"
    tiers_p = DATA / "tiers.json"
    if not stocks_p.exists():
        print(f"Missing: {stocks_p}", file=sys.stderr)
        return 1

    with stocks_p.open("r", encoding="utf-8") as f:
        stocks = json.load(f)

    # Build ticker -> today's tier map (prefer tiers.json which has all rows)
    tier_map: dict[str, str] = {}
    if tiers_p.exists():
        try:
            with tiers_p.open("r", encoding="utf-8") as f:
                tf = json.load(f)
            for r in tf.get("tiers", []):
                tier_map[r["ticker"]] = r["tier"]
        except Exception as e:
            print(f"  warn: couldn't read tiers.json ({e})", file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SHARE_DIR = ROOT / "web" / "public" / "share"
    SHARE_DIR.mkdir(parents=True, exist_ok=True)

    BASE_URL = "https://tickertier.vercel.app"
    count = 0
    html_tpl = (
        '<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8" />\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1" />\n'
        "<title>{title}</title>\n"
        '<meta name="description" content="{desc}" />\n'
        '<link rel="canonical" href="{canon}" />\n'
        '<meta property="og:type" content="article" />\n'
        '<meta property="og:title" content="{title}" />\n'
        '<meta property="og:description" content="{desc}" />\n'
        '<meta property="og:image" content="{img}" />\n'
        '<meta property="og:image:width" content="1200" />\n'
        '<meta property="og:image:height" content="630" />\n'
        '<meta property="og:url" content="{canon}" />\n'
        '<meta name="twitter:card" content="summary_large_image" />\n'
        '<meta name="twitter:title" content="{title}" />\n'
        '<meta name="twitter:description" content="{desc}" />\n'
        '<meta name="twitter:image" content="{img}" />\n'
        '<meta http-equiv="refresh" content="0;url={canon}" />\n'
        "<style>body{{font-family:system-ui;background:#f5f0e4;color:#0a0a0a;"
        "max-width:640px;margin:48px auto;padding:0 24px;line-height:1.5}}"
        "a{{color:#0a0a0a}}</style>\n</head>\n<body>\n"
        "<p>跳转到 <a href=\"{canon}\">{title}</a>…</p>\n"
        '<script>location.replace("{canon}");</script>\n'
        "</body>\n</html>\n"
    )

    for s in stocks:
        ticker = s.get("ticker")
        if not ticker:
            continue
        today_tier = tier_map.get(ticker)
        try:
            img = render(s, today_tier)
            out = OUT_DIR / f"stock-{ticker}.png"
            img.save(out, optimize=True)

            # Crawler-friendly stub
            name = s.get("name") or ticker
            pct = s.get("pct_change")
            try:
                pct_v = float(pct) * (100 if pct and -1.5 < float(pct) < 1.5 else 1)
                pct_str = f"{pct_v:+.2f}%"
            except Exception:
                pct_str = ""
            awards = s.get("awards_count") or 0
            title = f"{ticker} {name} · 夯股"
            desc_bits = []
            if today_tier:
                desc_bits.append(short_tier(today_tier))
            if pct_str:
                desc_bits.append(f"今日 {pct_str}")
            if awards:
                desc_bits.append(f"累计 {awards} 枚奖牌")
            desc = " · ".join(desc_bits) or "tickertier 股票颁奖典礼"
            html = html_tpl.format(
                title=title,
                desc=desc,
                canon=f"{BASE_URL}/stock/{ticker}",
                img=f"{BASE_URL}/og/stock-{ticker}.png",
            )
            (SHARE_DIR / f"stock-{ticker}.html").write_text(html, encoding="utf-8")
            count += 1
        except Exception as e:
            print(f"  FAIL {ticker}: {e}", file=sys.stderr)

    print(f"wrote {count} OG images to {OUT_DIR}")
    print(f"wrote {count} share stubs to {SHARE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
