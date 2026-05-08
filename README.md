# Stock Awards 🏆💩

给你的自选/持仓美股每天颁奖，评段位（夯死了 / 顶级 / 人上人 / NPC / 拉完了 / 答辩），做历史名人堂和 bar chart race。**主打娱乐，附带参考价值。**

## Quick Start

```bash
# 1. install (用 uv)
make install
source .venv/bin/activate

# 2. 一次性回溯过去 3 年
make seed

# 3. 起服务
make dev   # 前端 :3000 + API :8001
```

## 设计文档

- 实施计划：`~/.hermes/plans/2026-05-08-stock-awards-platform.md`
- 数据来源：yfinance（价格） + Finnhub（财报）
- 股票池：81 支 AI 基建美股（同步自 hermes skill `ai-infra-universe`）

## Tier 体系

🔥 夯死了 / 👑 顶级 / 💪 人上人 / 😐 NPC / 💩 拉完了 / ☠️ 答辩

## License

MIT (personal use)
