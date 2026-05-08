#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/logs"
LOCK_FILE="${STOCK_AWARDS_DAILY_LOCK:-/tmp/stock-awards-daily.lock}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily-$(date +%Y%m%d).log"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[$(date -Is)] daily pipeline already running; lock=$LOCK_FILE" | tee -a "$LOG_FILE"
  exit 1
fi

{
  echo "[$(date -Is)] stock-awards daily start"
  echo "root=$ROOT"
  cd "$ROOT"
  make daily
  echo "[$(date -Is)] stock-awards daily done"
} 2>&1 | tee -a "$LOG_FILE"
