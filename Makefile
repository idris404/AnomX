.PHONY: install test lint typecheck api worker dashboard docker-up docker-down db-migrate sample-data ingest-demo clean help nab-data retail-data nab-demo retail-demo postgres-demo

help:
	@echo AnomX — available targets:
	@echo   install      Sync all workspace dependencies with uv
	@echo   test         Run pytest across all packages
	@echo   lint         Run ruff linter
	@echo   typecheck    Run mypy strict on anomx core
	@echo   api          Start FastAPI dev server on port 8000
	@echo   worker       Start ARQ worker for async alert notifications
	@echo   dashboard    Start Streamlit dashboard on port 8501
	@echo   docker-up    Start Postgres and Redis containers
	@echo   docker-down  Stop and remove containers
	@echo   db-migrate   Apply Phase 1 Postgres migration (existing DBs)
	@echo   sample-data  Generate data/samples/example.csv
	@echo   ingest-demo  Ingest sample CSV into Postgres
	@echo   detect-demo  Ingest + run anomaly detection on sample_csv
	@echo   benchmark    Run synthetic benchmark and write reports/
	@echo   explain-demo Ingest + detect + show alert explanations
	@echo   nab-data       Download NAB sample CSV + labels
	@echo   retail-data    Generate Online Retail II-like sample CSV
	@echo   nab-demo       Download NAB sample + ingest + detect
	@echo   retail-demo    Generate retail sample + ingest + detect
	@echo   postgres-demo  Ingest hourly aggregate from sample_csv observations
	@echo   api-demo     explain-demo + curl-style API smoke hints
	@echo   clean        Remove caches and build artifacts

install:
	uv sync --all-packages --group dev

test:
	uv run pytest

lint:
	uv run ruff check packages/anomx services/api services/dashboard

typecheck:
	uv run mypy packages/anomx/anomx

api:
	uv run --no-sync --directory services/api uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	uv run --no-sync --directory services/api arq app.workers.settings.WorkerSettings

dashboard:
	uv run --no-sync --directory services/dashboard streamlit run app/main.py --server.port 8501

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

api-demo: explain-demo
	@echo Open http://localhost:8000/streams/sample_csv/alerts after `make api`

nab-data:
	uv run python scripts/download_nab_sample.py

retail-data:
	uv run python scripts/generate_online_retail_sample.py

nab-demo: nab-data
	uv run anomx ingest --config config/sources/nab_cpu_utilization.yaml
	uv run anomx detect --stream nab_cpu_utilization --config config/detectors.yaml

retail-demo: retail-data
	uv run anomx ingest --config config/sources/online_retail_daily.yaml
	uv run anomx detect --stream online_retail_daily --config config/detectors.yaml

postgres-demo: explain-demo
	uv run anomx ingest --config config/sources/postgres_observations_hourly.yaml
	uv run anomx detect --stream postgres_observations_hourly --config config/detectors.yaml

clean:
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist .mypy_cache rmdir /s /q .mypy_cache
	if exist .ruff_cache rmdir /s /q .ruff_cache
