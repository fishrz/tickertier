#!/usr/bin/env python3
"""Daily Telegram digest for tickertier.

Reads:
  web/public/data/today.json       - daily awards + tier distribution
  web/public/data/meta.json        - universe / awards / data_to
  web/public/data/stocks.json      - per-ticker close + pct_change (today vs prev)
  web/public/data/portfolio_positions.json  - real positions for personal PnL

Posts to Telegram (chat 8509167029) using the tickertier-writer skill's
A/B/C three-tier style: A=hook (~20%), B=data-driven personal (~50%),
C=professional facts (~30%).

Env:
  TELEGRAM_BOT_TOKEN  required
  TELEGRAM_CHAT_ID    default 8509167029
  DRY_RUN=1           print payload, don't send
  TG_SEED=N           deterministic template pick (default: hash of date)
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "web" / "public" / "data"
TODAY_JSON = DATA_DIR / "today.json"
META_JSON = DATA_DIR / "meta.json"
STOCKS_JSON = DATA_DIR / "stocks.json"
POSITIONS_JSON = DATA_DIR / "portfolio_positions.json"
CARD_PATH = DATA_DIR / "cards" / "daily-latest.png"
DEFAULT_CHAT_ID = "8509167029"
APP_URL = "https://tickertier.vercel.app/daily"

# ── Weekday in Chinese for header ─────────────────────────────────
_WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


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


def _format_pct(value: Any, with_sign: bool = True) -> str:
    """Format a pct. Accepts fractions (0.265 -> 26.5%) or already-percent (26.5)."""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if abs(n) <= 1:
        n *= 100
    if with_sign:
        sign = "+" if n > 0 else ""
        return f"{sign}{n:.1f}%"
    return f"{n:.1f}%"


def _format_dollar(value: float, signed: bool = True) -> str:
    sign = ""
    if signed:
        if value > 0:
            sign = "+"
        elif value < 0:
            sign = "-"
            value = abs(value)
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.2f}M"
    if value >= 10_000:
        return f"{sign}${value / 1_000:.1f}K"
    return f"{sign}${value:,.0f}"


def _format_date_header(date_str: str) -> str:
    """`2026-05-08` -> `5/8 周五`."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        wd = _WEEKDAY_CN[d.weekday()]
        return f"{d.month}/{d.day} {wd}"
    except Exception:
        return date_str


# ── Personal PnL: read positions + today's stocks ────────────────


def _compute_personal_pnl(
    today: dict[str, Any],
    stocks_by_ticker: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Compute today's dollar PnL for the real portfolio.

    Returns {pnl_usd, pnl_pct, market_value, winners, losers, top_pillar, top_traitor}
    or None if positions file is missing/invalid.
    """
    if not POSITIONS_JSON.exists():
        return None
    try:
        pf = _load_json(POSITIONS_JSON)
    except Exception:
        return None

    positions = pf.get("positions") or []
    if not positions:
        return None

    pnl_total = 0.0
    mv_total = 0.0
    winners = 0
    losers = 0
    contributions: list[tuple[str, float]] = []

    for pos in positions:
        ticker = pos.get("ticker")
        shares = float(pos.get("shares") or 0)
        if not ticker or shares <= 0:
            continue
        s = stocks_by_ticker.get(ticker)
        if not s:
            continue
        close = s.get("close")
        pct = s.get("pct_change")
        if close is None or pct is None:
            continue
        # d_price = close - prev_close = close - close / (1 + pct)
        denom = 1.0 + float(pct)
        if abs(denom) < 1e-9:
            continue
        prev_close = float(close) / denom
        d_price = float(close) - prev_close
        contrib = d_price * shares
        mv = float(close) * shares
        pnl_total += contrib
        mv_total += mv
        if d_price > 0:
            winners += 1
        elif d_price < 0:
            losers += 1
        contributions.append((ticker, contrib))

    if mv_total <= 0:
        return None

    pnl_pct = pnl_total / mv_total
    contributions.sort(key=lambda x: x[1], reverse=True)
    top_pillar = contributions[0] if contributions else None
    top_traitor = contributions[-1] if contributions and contributions[-1][1] < 0 else None

    return {
        "pnl_usd": pnl_total,
        "pnl_pct": pnl_pct,
        "market_value": mv_total,
        "winners": winners,
        "losers": losers,
        "position_count": winners + losers,
        "top_pillar": top_pillar,
        "top_traitor": top_traitor,
    }


# ── Template pools (A-tier hooks) ────────────────────────────────


def _hook_templates(
    king: dict[str, Any] | None,
    clown: dict[str, Any] | None,
    today: dict[str, Any],
    stocks_by_ticker: dict[str, dict[str, Any]],
) -> list[str]:
    """A-tier opening hook candidates. Caller picks one deterministically."""
    tpls: list[str] = []

    def _name_of(ticker: str | None) -> str:
        if not ticker:
            return ""
        s = stocks_by_ticker.get(ticker, {})
        return s.get("name") or ticker

    # 1) King with big move (>= +10%)
    if king:
        king_t = king.get("ticker")
        king_pct = king.get("metric")
        try:
            kp = float(king_pct or 0)
            if abs(kp) <= 1:
                kp *= 100
        except Exception:
            kp = 0
        if kp >= 15:
            tpls.append(f"{king_t} {_format_pct(king_pct)}，这哥们今天直接起飞，不带回头看的。")
            tpls.append(f"{king_t} {_format_pct(king_pct)}，它疯了，我们陪着一起疯。")
            tpls.append(f"{king_t} {_format_pct(king_pct)}，盘前没动静，盘中直接拉满。看不懂，但震撼。")
        elif kp >= 8:
            tpls.append(f"{king_t} {_format_pct(king_pct)}，稳得不像是 AI 股该有的样子。")
            tpls.append(f"{king_t} {_format_pct(king_pct)}，今天它是 81 只里最不需要解释的那一只。")
        elif kp >= 3:
            tpls.append(f"{king_t} {_format_pct(king_pct)}，没夸张的涨幅，但全场就它一个能看。")
            tpls.append(f"今日股王 {king_t} {_format_pct(king_pct)}，剩下 80 只在原地踏步。")

    # 2) Clown crash
    if clown:
        clown_t = clown.get("ticker")
        clown_pct = clown.get("metric")
        try:
            cp = float(clown_pct or 0)
            if abs(cp) <= 1:
                cp *= 100
        except Exception:
            cp = 0
        if cp <= -8:
            tpls.append(f"{clown_t} {_format_pct(clown_pct)}，没有任何消息，就这么自己崩了。")
            tpls.append(f"{clown_t} {_format_pct(clown_pct)}，它今天像故意来给大盘添堵的。")

    # 3) Tier distribution flavor
    dist = today.get("tier_distribution") or {}
    hot = dist.get("🔥 夯死了", 0)
    bad = dist.get("💩 拉完了", 0) + dist.get("☠️ 答辩", 0)
    npc = dist.get("😐 NPC", 0)
    if hot >= 8 and hot > bad:
        tpls.append(f"今天 {hot} 只夯死了。AI 股的春天又回来了，先别急着信。")
    elif bad >= 12:
        tpls.append(f"今天 {bad} 只拉胯。整个板块像约好了一起摆烂。")
    elif npc >= 30:
        tpls.append(f"今天 {npc} 只 NPC。市场在静音模式，全场没人愿意先开口。")

    # 4) Roller coaster award
    rc = _rank_one(_find_award(today, "roller_coaster"))
    if rc:
        rc_t = rc.get("ticker")
        rc_metric = rc.get("metric")
        try:
            rcp = float(rc_metric or 0)
            if abs(rcp) <= 1:
                rcp *= 100
            if rcp >= 20:
                tpls.append(f"{rc_t} 今天日内振幅 {rcp:.0f}%，一天给你演完一整年的剧情。")
        except Exception:
            pass

    # 5) Pump army (vol ratio explosion)
    pump = _rank_one(_find_award(today, "pump_army"))
    if pump:
        pmt = pump.get("ticker")
        pmm = pump.get("metric")
        try:
            pmv = float(pmm or 0)
            if pmv >= 3:
                tpls.append(f"{pmt} 今天成交量是 20 日均量的 {pmv:.1f} 倍。这背后肯定有事。")
        except Exception:
            pass

    # Always-on fallbacks if pool is empty
    if not tpls:
        if king:
            tpls.append(f"今日股王 {king.get('ticker')} {_format_pct(king.get('metric'))}。其他没啥大事。")
        else:
            tpls.append("今天市场基本没动静。NPC 们正常出勤。")

    return tpls


def _closer_templates(
    today: dict[str, Any],
    stocks_by_ticker: dict[str, dict[str, Any]],
    used_tickers: set[str],
) -> list[str]:
    """A-tier closing lines about a weird/notable ticker not used in the hook."""
    tpls: list[str] = []

    # comeback (绝地翻身) - someone clawed back from negative
    cb = _rank_one(_find_award(today, "comeback"))
    if cb and cb.get("ticker") not in used_tickers:
        cb_t = cb.get("ticker")
        cb_m = cb.get("metric")
        tpls.append(f"{cb_t} 今天绝地翻身 {_format_pct(cb_m)}，盘中跌得亲妈不认，最后还能爬回来。")

    # traitor (拖后腿)
    tr = _rank_one(_find_award(today, "traitor"))
    if tr and tr.get("ticker") not in used_tickers:
        tr_t = tr.get("ticker")
        tr_meta = tr.get("meta") or {}
        d_price = tr_meta.get("d_price")
        shares = tr_meta.get("shares")
        if d_price is not None and shares is not None:
            tpls.append(f"{tr_t} 今天一个人吃掉 {_format_dollar(float(d_price) * float(shares))}，今天最不想看到的那只。")
        else:
            tpls.append(f"{tr_t} 今天拖后腿冠军，一个人把均值拉下来。")

    # daily clown
    clown = _rank_one(_find_award(today, "daily_clown"))
    if clown and clown.get("ticker") not in used_tickers:
        ct = clown.get("ticker")
        cm = clown.get("metric")
        tpls.append(f"{ct} {_format_pct(cm)}，哥们你倒是说话呀，跌也跌得让人摸不着头脑。")

    # tear jerker (套牢)
    tj = _rank_one(_find_award(today, "tear_jerker"))
    if tj and tj.get("ticker") not in used_tickers:
        tj_t = tj.get("ticker")
        tpls.append(f"{tj_t} 又破套牢新低。它和持有它的人，今天都需要点温暖。")

    # NPC-flavored generic closer
    dist = today.get("tier_distribution") or {}
    npc = dist.get("😐 NPC", 0)
    if not tpls and npc >= 25:
        tpls.append(f"剩下 {npc} 只 NPC，明天见。")

    return tpls


# ── Message builder ──────────────────────────────────────────────


def build_message(today: dict[str, Any], meta: dict[str, Any]) -> str:
    date = today.get("date") or meta.get("data_to") or "unknown"
    date_header = _format_date_header(date)

    # Build stocks lookup once
    try:
        stocks_list = _load_json(STOCKS_JSON)
        if not isinstance(stocks_list, list):
            stocks_by_ticker = {}
        else:
            stocks_by_ticker = {s["ticker"]: s for s in stocks_list if "ticker" in s}
    except Exception:
        stocks_by_ticker = {}

    king = _rank_one(_find_award(today, "daily_king"))
    clown = _rank_one(_find_award(today, "daily_clown"))

    # Deterministic seed so the same day picks the same templates
    seed_env = os.environ.get("TG_SEED")
    seed = int(seed_env) if seed_env and seed_env.isdigit() else (
        int(hashlib.sha256(date.encode()).hexdigest()[:8], 16)
    )
    rng = random.Random(seed)

    # ── 1) Header
    lines: list[str] = [f"📅 *{date_header} · 夯股日报*", ""]

    # ── 2) A-tier hook (1 line)
    hooks = _hook_templates(king, clown, today, stocks_by_ticker)
    used_tickers: set[str] = set()
    if hooks:
        hook = rng.choice(hooks)
        lines.append(hook)
        lines.append("")
        # Track tickers used in hook to avoid repetition in closer
        for t in stocks_by_ticker.keys():
            if t in hook:
                used_tickers.add(t)

    # ── 3) C-tier data block
    if king:
        lines.append(f"🏆 股王: *{king.get('ticker')}* {_format_pct(king.get('metric'))}")
        used_tickers.add(king.get("ticker"))
    if clown:
        lines.append(f"💩 答辩: *{clown.get('ticker')}* {_format_pct(clown.get('metric'))}")
        used_tickers.add(clown.get("ticker"))

    # Tier distribution one-liner
    dist = today.get("tier_distribution") or {}
    universe = meta.get("universe") or sum(dist.values()) or "?"
    hot = dist.get("🔥 夯死了", 0)
    bad = dist.get("💩 拉完了", 0) + dist.get("☠️ 答辩", 0)
    if dist:
        lines.append(f"今日 {universe} 只: {hot} 只夯死了, {bad} 只拉胯, 其余在中间区域。")
    lines.append("")

    # ── 4) B-tier personal PnL
    pnl = _compute_personal_pnl(today, stocks_by_ticker)
    if pnl:
        pnl_usd = pnl["pnl_usd"]
        pnl_pct = pnl["pnl_pct"]
        wins = pnl["winners"]
        n = pnl["position_count"]
        verb = "今天" if pnl_usd >= 0 else "今天"
        lines.append(
            f"你的持仓: {_format_dollar(pnl_usd)} ({_format_pct(pnl_pct)}), "
            f"{n} 只里 {wins} 只收涨。"
        )

        # Pillar / traitor color
        pillar = pnl.get("top_pillar")
        traitor = pnl.get("top_traitor")
        if pillar and pillar[1] >= 100:
            pt, pv = pillar
            lines.append(f"顶梁柱 {pt} 贡献 {_format_dollar(pv)}。")
            used_tickers.add(pt)
        if traitor and traitor[1] <= -100:
            tt, tv = traitor
            lines.append(f"拖后腿 {tt} 吃掉 {_format_dollar(tv)}。")
            used_tickers.add(tt)
        lines.append("")

    # ── 5) A-tier closer (optional)
    closers = _closer_templates(today, stocks_by_ticker, used_tickers)
    if closers:
        lines.append(rng.choice(closers))
        lines.append("")

    # ── 6) Footer
    lines.append(f"🌐 {APP_URL}")

    # Collapse 3+ blank lines into 1
    out: list[str] = []
    prev_blank = False
    for ln in lines:
        is_blank = (ln == "")
        if is_blank and prev_blank:
            continue
        out.append(ln)
        prev_blank = is_blank
    return "\n".join(out).strip()


# ── Telegram I/O (unchanged) ─────────────────────────────────────


def send_photo(token: str, chat_id: str, photo_path: Path, caption: str) -> int:
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
        print(f"\n[card] {CARD_PATH} exists={CARD_PATH.exists()}")
        return 0

    if CARD_PATH.exists():
        rc = send_photo(token, chat_id, CARD_PATH, message)
        if rc == 0:
            return 0
        print("Photo send failed — falling back to text message", file=sys.stderr)

    return send_message(token, chat_id, message)


if __name__ == "__main__":
    raise SystemExit(main())
