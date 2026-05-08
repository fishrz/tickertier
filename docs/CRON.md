# Operations: Daily Pipeline and WSL Cron

This project has a one-command daily update path for the local DuckDB database.

## Manual daily run

From WSL:

```bash
cd /mnt/c/Users/YuRu/Documents/Projects/stock-awards
make daily
make health
```

`make daily` runs the pipeline in this order and fails fast if any step exits non-zero:

1. `fetch_prices --incremental`
2. `compute_metrics`
3. `fetch_earnings`
4. `compute_awards --daily`
5. `personas`

Each step prints ISO timestamps and elapsed seconds.

For logged/manual operation, use the shell wrapper:

```bash
./scripts/daily.sh
```

It writes to `logs/daily-YYYYMMDD.log` and uses a lock file at `/tmp/stock-awards-daily.lock` so two daily runs cannot write to DuckDB at the same time.

## Health check

```bash
make health
```

The health check prints `OK` when the latest database date has:

- price rows for the 81 stock universe (benchmark rows such as `QQQ` may make the count higher)
- daily awards for that date
- tier coverage for all 81 stock tickers

If something is missing, it exits non-zero and prints an `ISSUES` list.

## WSL cron setup

Edit the WSL user's crontab:

```bash
crontab -e
```

Add this weekday schedule:

```cron
# Stock Awards daily update, weekdays after US market close.
# If your WSL timezone is Asia/Shanghai, 21:30 ET is 09:30 the next calendar day during US daylight time.
30 21 * * 1-5 cd /mnt/c/Users/YuRu/Documents/Projects/stock-awards && /usr/bin/env bash scripts/daily.sh
```

If you want the job to run specifically in Eastern Time regardless of the WSL system timezone, set `CRON_TZ`:

```cron
CRON_TZ=America/New_York
30 21 * * 1-5 cd /mnt/c/Users/YuRu/Documents/Projects/stock-awards && /usr/bin/env bash scripts/daily.sh
```

## Verify cron is active

```bash
crontab -l
service cron status || sudo service cron start
```

After a scheduled run, inspect the log:

```bash
ls -lh /mnt/c/Users/YuRu/Documents/Projects/stock-awards/logs/
tail -n 80 /mnt/c/Users/YuRu/Documents/Projects/stock-awards/logs/daily-$(date +%Y%m%d).log
```

## Environment notes

- `make daily` uses `uv run`, so it can create/use the project virtual environment automatically.
- `fetch_earnings` uses `FINNHUB_API_KEY`. If the key is absent, `make daily` logs a warning and skips the earnings refresh so price/award/tier updates still run; add the key to cron when you want earnings refreshed in scheduled runs.
- DuckDB is single-writer. Do not bypass `scripts/daily.sh` for cron jobs; the wrapper's `flock` lock prevents concurrent daily runs.
