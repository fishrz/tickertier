.PHONY: install test seed daily api web dev clean

install:
	uv venv && uv pip install -e ".[dev]"

test:
	pytest -q

seed:  ## 一次性 3 年回溯
	python -m data.pipelines.compute_awards --backfill 2023-01-01

daily:  ## 每日增量 (美东收盘后)
	python -m data.pipelines.compute_awards --daily

api:
	uvicorn api.main:app --reload --port 8001

web:
	cd web && pnpm dev

dev:  ## 同时起前后端
	$(MAKE) -j2 api web

clean:
	rm -f data/awards.duckdb
	rm -rf .pytest_cache __pycache__
