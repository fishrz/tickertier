"""Final sanity checks for stock-awards backend."""
from data.db import get_conn

con = get_conn(read_only=True)


def show(title, sql, fmt=None):
    print(f"\n=== {title} ===")
    rows = con.execute(sql).fetchall()
    if not rows:
        print("  (empty)")
        return
    for r in rows:
        if fmt:
            print(" ", fmt(r))
        else:
            print(" ", r)


# 1. Coverage
show(
    "1a. Awards coverage by period",
    """SELECT period, count(distinct period_key) AS keys, count(*) AS rows
       FROM awards GROUP BY period ORDER BY period""",
)
show(
    "1b. Per-award row counts (all time)",
    """SELECT award_code, count(*) FROM awards GROUP BY 1 ORDER BY 2 DESC""",
)
show(
    "1c. Tier coverage",
    """SELECT min(date), max(date), count(distinct date), count(distinct ticker) FROM tiers""",
)

# 2. Today's awards
show(
    "2. Today's daily awards (2026-05-08)",
    """SELECT award_code, rank, ticker, round(metric*100, 2) AS pct
       FROM awards WHERE period='D' AND period_key='2026-05-08'
       ORDER BY award_code, rank""",
)

# 3. Today tier distribution
show(
    "3. Tier distribution 2026-05-08",
    """SELECT tier, count(*) FROM tiers WHERE date='2026-05-08' GROUP BY 1 ORDER BY 2 DESC""",
)

# 4. Most-decorated stocks (3 years, daily)
show(
    "4. Top decorated stocks (daily golds 3y)",
    """SELECT ticker, count(*) AS golds FROM awards
       WHERE period='D' AND rank=1 GROUP BY 1 ORDER BY 2 DESC LIMIT 10""",
)

# 5. 2025 劳模 winners
show(
    "5. Workhorse 2025 (yearly meta-award)",
    """SELECT rank, ticker, metric FROM awards
       WHERE award_code='workhorse' AND period='Y' AND period_key='2025'
       ORDER BY rank""",
)

# 6. Earnings awards
show(
    "6a. Earnings god total",
    """SELECT count(*) FROM awards WHERE award_code='earnings_god'""",
)
show(
    "6b. Earnings god last 3 events",
    """SELECT period_key, rank, ticker, round(metric*100, 2) AS pct
       FROM awards WHERE award_code='earnings_god'
       ORDER BY period_key DESC, rank LIMIT 9""",
)

# 7. Yearly steady_grind 2024 (Sharpe winners)
show(
    "7. Steady grind 2024 (Sharpe)",
    """SELECT rank, ticker, round(metric, 3) FROM awards
       WHERE award_code='steady_grind' AND period='Y' AND period_key='2024'
       ORDER BY rank""",
)

# 8. Empty awards (should be 0)
show(
    "8. Awards with 0 records (any?)",
    """WITH expected AS (
        SELECT 'daily_king' AS code UNION ALL SELECT 'daily_clown' UNION ALL
        SELECT 'roller_coaster' UNION ALL SELECT 'oscar' UNION ALL
        SELECT 'comeback' UNION ALL SELECT 'npc_god' UNION ALL
        SELECT 'pump_army' UNION ALL SELECT 'tank' UNION ALL
        SELECT 'reverse_idx' UNION ALL SELECT 'steady_grind' UNION ALL
        SELECT 'gambler' UNION ALL SELECT 'workhorse' UNION ALL
        SELECT 'silver_curse' UNION ALL SELECT 'earnings_god' UNION ALL
        SELECT 'earnings_clown' UNION ALL SELECT 'pillar' UNION ALL SELECT 'traitor'
       )
       SELECT e.code FROM expected e LEFT JOIN awards a ON a.award_code = e.code
       WHERE a.award_code IS NULL""",
)
