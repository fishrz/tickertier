"""Award metadata: name, joke, criterion (人话), formula (公式), category, unit.

`criterion` is the plain-language judging rule shown to users.
`formula` is the exact computation, surfaced in the modal for the technical types.
`category` groups awards in glossary / modal headers.
`unit` tells the front-end how to render the primary value: 'pct' / 'amp' / 'medals' / 'count' / 'amount'.
"""
from __future__ import annotations

AWARD_META: dict[str, dict[str, str]] = {
    # ── Daily awards ────────────────────────────────────────────
    "daily_king": {
        "name": "🏆 今日股王",
        "desc": "夯到飞起",
        "category": "daily",
        "unit": "pct",
        "criterion": "当天涨幅最大的那只股，简单粗暴。",
        "formula": "argmax (close − prev_close) / prev_close × 100，排除 QQQ 等基准。Top 3 上榜。",
    },
    "daily_clown": {
        "name": "💩 今日答辩",
        "desc": "建议退市",
        "category": "daily",
        "unit": "pct",
        "criterion": "当天跌得最惨的股，今天它最丢人。",
        "formula": "argmin (close − prev_close) / prev_close × 100，排除基准。Top 3 上榜。",
    },
    "roller_coaster": {
        "name": "🎢 过山车之王",
        "desc": "早上人上人，下午拉完了",
        "category": "daily",
        "unit": "amp",
        "criterion": "当天日内振幅最大的股，K 线像心电图。",
        "formula": "argmax (high − low) / prev_close × 100。",
    },
    "oscar": {
        "name": "🎭 影帝奖",
        "desc": "开盘装大佬，收盘装死",
        "category": "daily",
        "unit": "pct",
        "criterion": "开盘高开高走，收盘原形毕露。装得最像的就是影帝。",
        "formula": "在 gap > 0 的股票里，argmin fade，其中 fade = (close − high) / high × 100（值越负，从高点跌得越狠）。",
    },
    "comeback": {
        "name": "🪄 绝地翻身奖",
        "desc": "主打一个不装了",
        "category": "daily",
        "unit": "pct",
        "criterion": "盘中触底之后猛拉，最终收涨。主打一个绝地反击。",
        "formula": "在 pct_change > 0 的股票里，argmax rebound = (close − low) / low × 100。",
    },
    "npc_god": {
        "name": "💤 NPC 之光",
        "desc": "在的，活着，不动",
        "category": "daily",
        "unit": "amp",
        "criterion": "当天波澜不惊+成交量低迷的股，全场最 NPC。",
        "formula": "vol_ratio_20 < 0.7 的股里，argmin intraday_amp。即量能远低于 20 日均量、振幅又最小的那只。",
    },
    "pump_army": {
        "name": "📈 暴兵奖",
        "desc": "主力进场了家人们",
        "category": "daily",
        "unit": "count",
        "criterion": "上涨日里量能爆发最猛的，疑似主力进场。",
        "formula": "在 pct_change > 0 的股票里，argmax vol_ratio_20 = volume / 20日均量。值是几就代表是平均量的几倍。",
    },
    "tank": {
        "name": "🛡️ 抗揍奖",
        "desc": "大盘崩我不崩，反向 indicator 王",
        "category": "daily",
        "unit": "pct",
        "criterion": "大盘明显下跌的日子里，跌得最少甚至上涨的那只。",
        "formula": "前提：QQQ pct_change ≤ −0.5%。在该条件下取 argmax(ticker.pct_change − QQQ.pct_change)。QQQ 不下跌当天本奖空缺。",
    },
    # ── Periodic awards ────────────────────────────────────────
    "reverse_idx": {
        "name": "🪦 反指奖",
        "desc": "陪跑十级运动员",
        "category": "periodic",
        "unit": "pct",
        "criterion": "周期内跟 QQQ 走势最反着来的股，标准的反指。",
        "formula": "在 ≥ N 个交易日的窗口里，按日级 pct_change 与 QQQ 计算 Pearson 相关系数，取最负的那只。",
    },
    "steady_grind": {
        "name": "🐢 细水长流奖",
        "desc": "老老实实赚钱",
        "category": "periodic",
        "unit": "pct",
        "criterion": "周期内涨幅稳健、波动又小的股。不靠暴涨，靠长跑。",
        "formula": "周期累计收益 / 日级收益标准差（年化），即 Sharpe-like ratio，取最大值。",
    },
    "gambler": {
        "name": "🎰 赌狗之友奖",
        "desc": "心脏起搏器赞助商",
        "category": "periodic",
        "unit": "amp",
        "criterion": "周期内累计振幅最大的股，最适合心跳爱好者。",
        "formula": "Σ intraday_amp_t over period，取 sum 最大的 ticker。",
    },
    "workhorse": {
        "name": "🏅 劳模奖",
        "desc": "奖项收割机",
        "category": "periodic",
        "unit": "medals",
        "criterion": "周期内拿过最多日度金牌的股，奖项含金量直接拉满。",
        "formula": "count(awards where rank=1 AND period='D' AND date in period) GROUP BY ticker，取最高。",
    },
    "silver_curse": {
        "name": "🪑 万年老二奖",
        "desc": "一人之下万人之上的疲惫感",
        "category": "periodic",
        "unit": "medals",
        "criterion": "周期内拿了最多次「亚军」的股。永远第二，痛并快乐。",
        "formula": "count(awards where rank=2 AND period='D' AND date in period) GROUP BY ticker。",
    },
    # ── Earnings awards ────────────────────────────────────────
    "earnings_god": {
        "name": "💼 财报封神",
        "desc": "数字会自己说话",
        "category": "earnings",
        "unit": "pct",
        "criterion": "财报次日跳得最猛的股，业绩直接干到位。",
        "formula": "next_day_pct = (T+1 close − T close) / T close × 100，T 为财报披露日。取最大值。",
    },
    "earnings_clown": {
        "name": "💼 财报现形",
        "desc": "原形毕露",
        "category": "earnings",
        "unit": "pct",
        "criterion": "财报次日跌得最惨的股，业绩直接破防。",
        "formula": "next_day_pct = (T+1 close − T close) / T close × 100，取最小值。",
    },
    # ── Portfolio awards ───────────────────────────────────────
    "pillar": {
        "name": "💰 顶梁柱奖",
        "desc": "全家就指望你了",
        "category": "portfolio",
        "unit": "amount",
        "criterion": "持仓中按真实仓位加权后，对账户当日盈亏贡献最大的股。",
        "formula": "argmax (shares × close × pct_change / 100)。即仓位 × 涨跌的金额贡献，越正越顶。",
    },
    "traitor": {
        "name": "🩸 拖后腿奖",
        "desc": "建议清仓谢罪",
        "category": "portfolio",
        "unit": "amount",
        "criterion": "持仓中按真实仓位加权后，对账户拖累最大的股。",
        "formula": "argmin (shares × close × pct_change / 100)，金额负得最多。",
    },
    "cash_king": {
        "name": "💸 钞能力之王",
        "desc": "实打实赚到钱的那个",
        "category": "portfolio",
        "unit": "amount",
        "criterion": "持仓中累计浮盈金额最大的股。涨幅再猛，仓位小也白搭；这奖只看真金白银。",
        "formula": "argmax (last_close − avg_cost) × shares，仅取浮盈 > 0 的持仓。",
    },
    "tear_jerker": {
        "name": "😭 我的眼泪奖",
        "desc": "套牢套到亲妈不认",
        "category": "portfolio",
        "unit": "amount",
        "criterion": "持仓中累计浮亏金额最深的股。看一次哭一次。",
        "formula": "argmin (last_close − avg_cost) × shares，仅取浮亏 < 0 的持仓。",
    },
    "big_position": {
        "name": "👑 仓位之王",
        "desc": "你就是我的全部",
        "category": "portfolio",
        "unit": "pct",
        "criterion": "占整个账户市值比例最高的持仓。压舱石 or 单吊一注，一目了然。",
        "formula": "argmax (shares × last_close) / Σ(shares × last_close) × 100。",
    },
    "buy_low": {
        "name": "🧠 人间清醒奖",
        "desc": "买在脚踝上的天选之子",
        "category": "portfolio",
        "unit": "pct",
        "criterion": "成本价相对当前价折扣最大的持仓。证明你那次出手是真的清醒。",
        "formula": "argmax (last_close − avg_cost) / avg_cost × 100，仅取浮盈 > 0。",
    },
}


def meta_for(code: str) -> dict[str, str]:
    return AWARD_META.get(code, {"name": code, "desc": ""})
