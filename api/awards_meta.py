"""Award metadata for human-friendly names + descriptions."""
AWARD_META: dict[str, dict[str, str]] = {
    "daily_king":    {"name": "🏆 今日股王",     "desc": "夯到飞起"},
    "daily_clown":   {"name": "💩 今日答辩",     "desc": "建议退市"},
    "roller_coaster":{"name": "🎢 过山车之王",   "desc": "早上人上人，下午拉完了"},
    "oscar":         {"name": "🎭 影帝奖",       "desc": "开盘装大佬，收盘装死"},
    "comeback":      {"name": "🪄 绝地翻身奖",   "desc": "主打一个不装了"},
    "npc_god":       {"name": "💤 NPC 之光",     "desc": "在的，活着，不动"},
    "pump_army":     {"name": "📈 暴兵奖",       "desc": "主力进场了家人们"},
    "tank":          {"name": "🛡️ 抗揍奖",       "desc": "大盘红我绿，反向 indicator 王"},
    "reverse_idx":   {"name": "🪦 反指奖",       "desc": "陪跑十级运动员"},
    "steady_grind":  {"name": "🐢 细水长流奖",   "desc": "老老实实赚钱"},
    "gambler":       {"name": "🎰 赌狗之友奖",   "desc": "心脏起搏器赞助商"},
    "workhorse":     {"name": "🏅 劳模奖",       "desc": "奖项收割机"},
    "silver_curse":  {"name": "🪑 万年老二奖",   "desc": "一人之下万人之上的疲惫感"},
    "earnings_god":  {"name": "💼 财报封神",     "desc": "数字会自己说话"},
    "earnings_clown":{"name": "💼 财报现形",     "desc": "原形毕露"},
    "pillar":        {"name": "💰 顶梁柱奖",     "desc": "全家就指望你了"},
    "traitor":       {"name": "🩸 拖后腿奖",     "desc": "建议清仓谢罪"},
}


def meta_for(code: str) -> dict[str, str]:
    return AWARD_META.get(code, {"name": code, "desc": ""})
