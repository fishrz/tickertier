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

## Operations

每日更新链路：

```bash
make daily   # fetch_prices -> compute_metrics -> fetch_earnings -> compute_awards -> personas
make health  # 检查最新 prices / daily awards / 81 ticker tier 覆盖
```

Cron 包装脚本：

```bash
./scripts/daily.sh
```

它会写 `logs/daily-YYYYMMDD.log`，并用 `/tmp/stock-awards-daily.lock` 防止 DuckDB 并发写入。WSL crontab 示例见 `docs/CRON.md`。

## License

MIT (personal use)
