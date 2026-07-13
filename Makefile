.PHONY: install test lint typecheck api docker-up docker-down db-migrate sample-data ingest-demo clean help

help:
	@echo AnomX — available targets:
	@echo   install      Sync all workspace dependencies with uv
	@echo   test         Run pytest across all packages
	@echo   lint         Run ruff linter
	@echo   typecheck    Run mypy strict on anomx core
	@echo   api          Start FastAPI dev server on port 8000
	@echo   docker-up    Start Postgres and Redis containers
	@echo   docker-down  Stop and remove containers
	@echo   db-migrate   Apply Phase 1 Postgres migration (existing DBs)
	@echo   sample-data  Generate data/samples/example.csv
	@echo   ingest-demo  Ingest sample CSV into Postgres
	@echo   detect-demo  Ingest + run anomaly detection on sample_csv
	@echo   benchmark    Run synthetic benchmark and write reports/
	@echo   explain-demo Ingest + detect + show alert explanations
	@echo   clean        Remove caches and build artifacts

install:
	uv sync --all-packages --group dev

test:
	uv run pytest

lint:
	uv run ruff check packages/anomx services/api

typecheck:
	uv run mypy packages/anomx/anomx

api:
	uv run --directory services/api uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

docker-up:
	docker compose up -d

docker-down:
	docker compose down

db-reset:
	docker compose down -v
	docker compose up -d

db-migrate:
	docker exec -i anomx-postgres psql -U anomx -d anomx < infra/postgres/migrations/001_phase1_ingestion.sql

sample-data:
	uv run python scripts/generate_sample_csv.py

ingest-demo: sample-data
	uv run anomx ingest --config config/sources/sample_csv.yaml

detect-demo: ingest-demo
	uv run anomx detect --stream sample_csv --config config/detectors.yaml

benchmark:
	uv run anomx benchmark --config config/benchmark.yaml

explain-demo: detect-demo
	uv run anomx explain --stream sample_csv --limit 3

clean:
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist .mypy_cache rmdir /s /q .mypy_cache
	if exist .ruff_cache rmdir /s /q .ruff_cache
