CREATE TABLE IF NOT EXISTS prices (
  ticker TEXT, date DATE,
  open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE, volume BIGINT,
  PRIMARY KEY (ticker, date)
);
CREATE TABLE IF NOT EXISTS daily_metrics (
  ticker TEXT, date DATE,
  pct_change DOUBLE, intraday_amp DOUBLE, gap DOUBLE,
  rebound DOUBLE, fade DOUBLE, vol_ratio_20 DOUBLE, std_5 DOUBLE,
  PRIMARY KEY (ticker, date)
);
CREATE TABLE IF NOT EXISTS earnings (
  ticker TEXT, report_date DATE, fiscal_period DATE,
  eps_actual DOUBLE, eps_est DOUBLE, surprise DOUBLE, surprise_pct DOUBLE,
  next_day_pct DOUBLE,
  PRIMARY KEY (ticker, report_date)
);
CREATE TABLE IF NOT EXISTS awards (
  award_code TEXT, period TEXT, period_key TEXT,
  rank INTEGER, ticker TEXT, metric DOUBLE, meta JSON,
  PRIMARY KEY (award_code, period, period_key, rank)
);
CREATE TABLE IF NOT EXISTS tiers (
  ticker TEXT, date DATE, tier TEXT, score DOUBLE, rank_pct DOUBLE,
  PRIMARY KEY (ticker, date)
);
CREATE TABLE IF NOT EXISTS positions (
  date DATE, ticker TEXT, shares DOUBLE, avg_cost DOUBLE,
  PRIMARY KEY (date, ticker)
);
CREATE TABLE IF NOT EXISTS personas (
  ticker TEXT PRIMARY KEY, persona TEXT, tier_dist JSON, updated_at TIMESTAMP
);
