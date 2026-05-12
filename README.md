<div align="center">

# tickertier
### 夯股 · the daily tier-list for your tickers

**[中文](./README.md)** · [English](./README.en.md)

每天给你的股票颁奖，按 tier 排座次。
🔥 夯死了 → 👑 顶级 → 💪 人上人 → 😐 NPC → 💩 拉完了 → ☠️ 答辩

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Made with uv](https://img.shields.io/badge/made%20with-uv-7a3fff)](https://github.com/astral-sh/uv)
[![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20DuckDB-009688)]()
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite%20%2B%20D3-61dafb)]()
[![Personal Use](https://img.shields.io/badge/use-personal-blue)]()

![home](docs/img/home.png)

</div>

---

## 故事是这样的

我盯了半年 AI 基建美股。81 支票，从 NVDA 这种谁都认识的，到一些光通信、HBM、EDA、网络芯片里的小角色，每天开盘到收盘我都得扫一遍。

盯着盯着我发现一个事，**这 81 支票每天的剧情比电视剧还精彩**。

有的高开低走，开盘装大佬，收盘装死，活脱脱一个影帝。有的早盘装死，下午原地起飞，主打一个不装了。有的振幅 20% 最后收平，给你来个完整过山车，下来腿都软。还有那种全天不动如山、量也没有、振幅个位数的，你打开盘后图都怀疑是不是数据没刷新，结果它就是在那活着。

某天我盯着满屏红绿数字，突然想，与其每天瞪着这些数字焦虑，**不如给它们颁个奖**。

今日股王、今日答辩、绝地翻身奖、影帝奖、NPC 之光、银河诅咒。。。一边写名字一边乐，越写越觉得这事儿好玩。

于是有了这个东西，叫 **tickertier**，中文名 **夯股**。

它不是一个严肃的投资工具。它就是一层套在真实行情上的娱乐皮，把你每天的盯盘体验从「焦虑刷新」变成「准时看一场颁奖典礼」。仅此而已。

---

## 长这样

<table>
<tr>
<td width="50%"><b>🎭 今日颁奖之夜</b><br/>13 个奖一次发完，下方 tier 榜把全宇宙切六档排队<br/><img src="docs/img/home.png"/></td>
<td width="50%"><b>📊 持仓战报</b><br/>真持仓 → 顶梁柱 / 拖后腿 / 仓位之王 / 我的眼泪<br/><img src="docs/img/portfolio.png"/></td>
</tr>
<tr>
<td width="50%"><b>🏛️ 名人堂</b><br/>累计奖牌榜 + 8 种人格分类（财报戏精 / NPC 系列 / ...）<br/><img src="docs/img/hall.png"/></td>
<td width="50%"><b>🏁 排名变迁 Race</b><br/>D3 bar chart race，可调速、可拖时间轴<br/><img src="docs/img/race.png"/></td>
</tr>
</table>

---

## 22 个奖项

奖项分三类，日常奖每天评，周期奖按周/月/季评，持仓奖只有当你配了 `data/portfolio.json` 才会出现。

### 日常奖 (8)

| 奖项 | 怎么算 | 文案 |
|---|---|---|
| 🏆 今日股王 | 当日涨幅 #1 | 夯到飞起 |
| 💩 今日答辩 | 当日跌幅 #1 | 建议退市 |
| 🪄 绝地翻身奖 | 日内最低 → 收盘反弹幅度 | 主打一个不装了 |
| 🎢 过山车之王 | 日内振幅 (high-low)/open | 早上人上人，下午拉完了 |
| 🎭 影帝奖 | 高开低走，最高 → 收盘跌幅 | 开盘装大佬，收盘装死 |
| 💤 NPC 之光 | 振幅 + 量能双低 | 在的，活着，不动 |
| 📈 暴兵奖 | 量能 / 20 日均量 | 主力进场了家人们 |
| 🛡️ 抗跌之王 | QQQ 下跌日里逆势上涨 | 跌的不是我跌的是大盘 |

### 周期奖 (7)

| 奖项 | 周期 | 怎么算 |
|---|---|---|
| 🐎 劳模奖 | 月/季/年 | 阳线天数最多 |
| 🧘 稳如老狗 | 月/季 | 累计正收益 + std 最低 |
| 🎰 赌徒之王 | 周/月 | 累计振幅最大 |
| 💰 财报赢家 | 单次 earnings | 财报后 1d 涨幅 |
| 😱 财报翻车 | 单次 earnings | 财报后 1d 跌幅 |
| 🪞 反指奖 | 月/季 | 跟跌不跟涨（上行 β 低、下行 β 高） |
| 💀 银河诅咒 | 任意 | 连续阴线最多天数 |

### 持仓奖 (6) ｜ 仅在配置 `data/portfolio.json` 后启用

| 奖项 | 怎么算 |
|---|---|
| 💰 顶梁柱 | 当日盈利贡献 #1 |
| 🩸 拖后腿 | 当日亏损贡献 #1 |
| 💸 钞能力之王 | 累计浮盈 #1 |
| 😭 我的眼泪奖 | 累计浮亏 #1 |
| 👑 仓位之王 | 持仓占账户百分比 #1 |
| 🧠 人间清醒奖 | 相对成本回报率 #1（买在脚踝上的天选之子） |

---

## 六档 tier

颁完奖之后，全 universe 按当日综合表现切六档。这套档位不是按 Sharpe ratio 算的，是按情绪强度切的。

```
🔥 夯死了    顶配，今天就是它的主场
👑 顶级      涨得很爽，但还没到夯死
💪 人上人    稳稳跑赢平均
😐 NPC       不悲不喜，活着
💩 拉完了    今天有点惨
☠️ 答辩      惨烈级别，需要拎出来单独哀悼
```

为什么不是 5 档而是 6 档，最早是 5 档（夯/顶/人上人/NPC/拉），后来发现真正惨烈的票（-10% 起步）和「普通拉」在情感强度上完全不是一个东西，必须独立拎出来叫「☠️ 答辩」，要不然对不起它今天受的苦。

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
- **人格分类**：KMeans 把 81 支股按多维表现指标聚成 8 个 persona（财报戏精 / NPC 系列 / 稳健型选手 / 大起大落型 ……）

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

## 每日运维

```bash
make daily    # fetch_prices → compute_metrics → fetch_earnings → compute_awards → personas
make health   # 检查最新 prices / daily awards / 全 universe tier 覆盖
```

挂 cron 每天美东收盘后跑：

```bash
./scripts/daily.sh
```

写 `logs/daily-YYYYMMDD.log`，用 `/tmp/stock-awards-daily.lock` 防 DuckDB 并发写。WSL crontab 示例见 [`docs/CRON.md`](docs/CRON.md)。

---

## 项目结构

```
tickertier/
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

## 几个不太一样的设计选择

**为什么 DuckDB 不是 Postgres**
80 支股 × 3 年 ≈ 60k 行，单文件 50MB，全部 SQL 跑分析比起 server 数据库轻 100 倍。回溯 + 跨期聚合是 DuckDB 的主场，零运维成本，启动即可用。这种规模上根本用不着 Postgres，用了反而是负担。

**为什么不做用户系统、不做票选**
单人版 2 周能跑通，加上登录注册 + 反作弊 + 内容审核就是 3 倍工期。这个项目的乐趣在于「我自己挑的票今天获得了什么奖」，不在于「全网投票」。先把单人体验打磨到爽，多人版本以后再说。

**为什么奖项名一定要中二**
娱乐感来自人话，不来自 Sharpe ratio。「今日答辩」和「Bottom Performer」在数学上是一样的，但只有前一个会让你想截图发朋友圈。一个工具好不好玩，名字占一半。

**为什么是 6 档不是 5 档**
最早设计 5 档（夯/顶/人上人/NPC/拉），跑了一周发现真正惨烈的票（-10% 起步）和普通的「拉」在情感强度上完全不是一个东西。如果不把它们拎出来单独叫「☠️ 答辩」，整个 tier 表的张力会松一半。

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
| 包管理 | uv · pnpm |

---

## License

MIT，个人使用。

---

<sub>⚠️ <b>免责声明</b>：本平台所有奖项、tier、文案、人格分类均为娱乐用途，<b>不构成任何投资建议</b>。买卖决策请基于你自己的研究和风险承受能力。POWERED BY DUCKDB · YFINANCE · FINNHUB</sub>
