<div align="center">

# 夯榜 · Stock Awards 🎖️

**给你的自选/持仓美股每天颁奖。**
夯死了 → 顶级 → 人上人 → NPC → 拉完了 → 答辩。
主打娱乐，附带参考价值。

![home](docs/img/home.png)

</div>

---

## 这是什么

一个把"每天盯盘"变成"每天颁奖典礼"的本地 web app。

我盯了半年 AI 基建美股，发现 **80 多支标的每天的剧情比电视剧还精彩** —— 有的高开低走（影帝），有的早盘装死下午原地起飞（绝地翻身），有的振幅 20% 收平（过山车之王）。看着看着就想：与其每天瞪着红绿数字，不如给它们颁个奖。

于是有了这个：

- **22 个奖项**，每天自动评选，名字全是网络梗（"今日答辩"、"NPC 之光"、"我的眼泪奖"）
- **6 档 tier 体系**，把 81 支股票按当日综合表现切档分配
- **名人堂**，看哪只票历史上拿了多少金银铜
- **Bar Chart Race**，年度颁奖典礼风格，看排名一帧帧变迁
- **持仓战报**，按你真实持仓单独算 6 个奖（顶梁柱 / 拖后腿 / 钞能力 / ...）

数据全部来自真实行情（yfinance + Finnhub），但**严肃性为零，娱乐性满分**。

---

## 截图

<table>
<tr>
<td width="50%"><b>🎭 今日颁奖之夜</b><br/>13 个奖一次发完，下方 tier 榜把 81 支股切六档<br/><img src="docs/img/home.png"/></td>
<td width="50%"><b>📊 持仓战报</b><br/>真持仓 → 顶梁柱 / 拖后腿 / 仓位之王<br/><img src="docs/img/portfolio.png"/></td>
</tr>
<tr>
<td width="50%"><b>🏛️ 名人堂</b><br/>累计奖牌榜 + 8 种人格分类（Earnings Drama Queen / NPC 系列 / ...）<br/><img src="docs/img/hall.png"/></td>
<td width="50%"><b>🏁 排名变迁 Race</b><br/>D3 bar chart race，可调速、可拖时间轴<br/><img src="docs/img/race.png"/></td>
</tr>
</table>

---

## 22 个奖项

### 日常奖 (8)
| 奖项 | 标准 | 文案 |
|---|---|---|
| 🏆 今日股王 | 当日涨幅 #1 | 夯到飞起 |
| 💩 今日答辩 | 当日跌幅 #1 | 建议退市 |
| 🪄 绝地翻身奖 | 日内最低 → 收盘反弹幅度 | 主打一个不装了 |
| 🎢 过山车之王 | 日内振幅 (high-low)/open | 早上人上人，下午拉完了 |
| 🎭 影帝奖 | 高开低走，最高 → 收盘跌幅 | 开盘装大佬，收盘装死 |
| 💤 NPC 之光 | 振幅 + 量能双低 | 在的，活着，不动 |
| 📈 暴兵奖 | 量能 / 20 日均量 | 主力进场了家人们 |
| 🛡️ 抗跌之王 | QQQ 红盘日里逆势上涨 | 跌的不是我跌的是大盘 |

### 周期奖 (7)
| 奖项 | 周期 | 标准 |
|---|---|---|
| 🐎 劳模奖 | 月/季/年 | 阳线天数最多 |
| 🧘 稳如老狗 | 月/季 | 累计正收益 + std 最低 |
| 🎰 赌徒之王 | 周/月 | 累计振幅最大 |
| 💰 财报赢家 | 单次 earnings | 财报后 1d 涨幅 |
| 😱 财报翻车 | 单次 earnings | 财报后 1d 跌幅 |
| 🪞 反指奖 | 月/季 | 跟跌不跟涨（上行 β 低、下行 β 高） |
| 💀 银河诅咒 | 任意 | 连续阴线最多天数 |

### 持仓奖 (6) ｜ 仅在配置 `data/portfolio.json` 后启用
| 奖项 | 标准 |
|---|---|
| 💰 顶梁柱奖 | 当日盈利贡献 #1 |
| 🩸 拖后腿奖 | 当日亏损贡献 #1 |
| 💸 钞能力之王 | 累计浮盈 #1 |
| 😭 我的眼泪奖 | 累计浮亏 #1 |
| 👑 仓位之王 | 持仓占账户百分比 #1 |
| 🧠 人间清醒奖 | 相对成本回报率 #1（买在脚踝上的天选之子） |

---

## 架构

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   yfinance      │────▶│              │     │   FastAPI       │
│   Finnhub       │     │   DuckDB     │◀───▶│   :8001         │
└─────────────────┘     │   .duckdb    │     └────────┬────────┘
                        │              │              │
┌─────────────────┐     │  prices      │              │  REST
│  pipelines/     │────▶│  earnings    │              ▼
│  fetch_prices   │     │  metrics     │     ┌─────────────────┐
│  compute_metrics│     │  awards      │     │  React + Vite   │
│  compute_awards │     │  personas    │     │  Tailwind       │
│  fetch_earnings │     │  tiers       │     │  D3 / Recharts  │
│  personas (KMeans)    │              │     │  :3000          │
└─────────────────┘     └──────────────┘     └─────────────────┘
       ▲
       │  cron daily
       │
   scripts/daily.sh
```

- **数据层**：DuckDB 单文件，所有计算用 SQL/pandas 在本地跑，零外部依赖
- **算法层**：每个奖项一个 Python 模块（`data/awards/<bucket>/<award>.py`），实现 `compute(date) -> [Winner]` 接口，由 `registry.py` 注册
- **API 层**：FastAPI 4 个 route（awards / stocks / race / portfolio）
- **前端**：React + Vite + Tailwind，杂志/报刊视觉语言，4 个主页面 + 个股详情页
- **人格分类**：KMeans 把 81 支股按多维表现指标聚成 8 个 persona（Earnings Drama Queen、NPC 系列、稳健型选手、大起大落选手 ……）

---

## Quick Start

```bash
# 1. 装依赖（用 uv，比 pip 快 10x）
make install
source .venv/bin/activate

# 2. 配置股票池
cp data/universe.example.json data/universe.json
# 编辑成你自己的 ticker 列表

# 3. 配置持仓（可选，启用持仓奖）
cp data/portfolio.example.json data/portfolio.json
# 填入持仓数量、成本

# 4. 一次性回溯过去 3 年（约 10 分钟，看你池子大小）
make seed

# 5. 起服务
make dev      # 前端 :3000 + API :8001 同时起
```

打开 http://localhost:3000，开始看戏。

---

## Operations

### 每日更新链路

```bash
make daily    # fetch_prices → compute_metrics → fetch_earnings → compute_awards → personas
make health   # 检查最新 prices / daily awards / 全 universe tier 覆盖
```

### Cron 自动跑

```bash
./scripts/daily.sh
```

写 `logs/daily-YYYYMMDD.log`，用 `/tmp/stock-awards-daily.lock` 防 DuckDB 并发写。WSL crontab 示例见 [`docs/CRON.md`](docs/CRON.md)。

---

## 项目结构

```
stock-awards/
├── api/                  # FastAPI 后端
│   ├── routes/           # awards / stocks / race / portfolio
│   ├── awards_meta.py    # 奖项元数据（名字、文案、规则说明）
│   └── tests/
├── data/
│   ├── awards/           # 22 个奖项算法
│   │   ├── daily/        # 8 个日常奖
│   │   ├── periodic/     # 7 个周期奖
│   │   ├── portfolio/    # 6 个持仓奖
│   │   ├── tier.py       # 六档 tier 切档
│   │   └── registry.py   # 奖项注册表
│   ├── pipelines/        # 数据管道（fetch / compute）
│   ├── universe.json     # 你的自选股池（gitignored）
│   └── portfolio.json    # 你的真实持仓（gitignored）
├── web/                  # React 前端
│   └── src/pages/        # Today / Hall / Race / Portfolio / StockDetail
├── scripts/
│   ├── daily.sh          # cron 入口
│   └── seed.sh           # 3 年回溯
├── docs/
│   ├── CRON.md
│   └── img/              # README 截图
└── reports/              # 验收报告 / smoke tests
```

---

## 设计与决策

- **为什么 DuckDB 不是 Postgres**：80 支股 × 3 年 ≈ 60k 行，单文件 50MB，全部 SQL 跑分析比起 server 数据库轻 100 倍。回溯 + 跨期聚合是 DuckDB 的主场。
- **为什么不做用户系统 / 票选**：单人版 2 周能跑通，加上登录注册 + 反作弊 + 内容审核就是 3 倍工期。先把单人体验打磨到爽再说。
- **为什么奖项名要中二**：娱乐感来自**人话**而不是 Sharpe ratio。"今日答辩" 和 "Bottom Performer" 在严肃性上一致，但只有前一个会让你想截图发朋友圈。
- **为什么 tier 表分 6 档不是 5**：原本设计 5 档（夯/顶/人上人/NPC/拉），后来发现真正惨烈的票（-10% 起步）和"普通拉"在情感强度上完全不同，必须独立拎出来叫"☠️ 答辩"。

详细实施计划：`~/.hermes/plans/2026-05-08-stock-awards-platform.md`。

---

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.11 · FastAPI · pydantic v2 |
| 数据库 | DuckDB |
| 行情/财报 | yfinance · finnhub-python |
| 调度 | cron + flock |
| 前端 | React 18 · Vite · TypeScript · Tailwind CSS |
| 图表 | Recharts (常规) · D3 (bar chart race) |
| 测试 | pytest · vitest |
| 包管理 | uv |

---

## License

MIT (personal use)

---

<sub>免责声明：本平台所有奖项、tier、文案均为娱乐用途，**不构成任何投资建议**。POWERED BY DUCKDB · YFINANCE · FINNHUB</sub>
