SHELL := /bin/bash
.PHONY: install test seed daily health api web dev clean

install:
	uv venv && uv pip install -e ".[dev]"

test:
	uv run pytest -q

seed:  ## 一次性 3 年回溯
	uv run python -m data.pipelines.compute_awards --backfill 2023-01-01

daily:  ## 每日增量 (美东收盘后)
	uv run python scripts/run_daily.py

health:  ## 检查最新 prices / awards / 81 ticker tier 覆盖
	uv run python -m scripts.health

api:
	uv run uvicorn api.main:app --reload --port 8001

web:
	cd web && pnpm dev

dev:  ## 同时起前后端
	$(MAKE) -j2 api web

clean:
	rm -f data/awards.duckdb
	rm -rf .pytest_cache __pycache__
