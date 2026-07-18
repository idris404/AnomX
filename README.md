# AnomX

Pluggable anomaly detection engine for time series and tabular data.

## Prerequisites (Windows)

Install these tools and ensure they are on your PATH:

1. **Python 3.11** — pinned via `.python-version`
2. **[uv](https://docs.astral.sh/uv/)** — dependency manager
3. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** — PostgreSQL, Redis, Redpanda
4. **GNU Make** — via GnuWin32:
   ```powershell
   winget install GnuWin32.Make
   ```
   Restart PowerShell after installation so `make` is recognized.

## Quick Start

```powershell
cd AnomX
make install
make docker-up
make test
make polish-demo
```

Terminal 1 — API:

```powershell
make api
```

Terminal 2 — Dashboard:

```powershell
make dashboard
```

Open http://127.0.0.1:8501 (Overview, Alerts, Runs tabs).

## Project Structure

```
packages/anomx/          # Core library (publishable, no web deps)
services/api/            # FastAPI REST + Prometheus /metrics
services/dashboard/      # Streamlit operator UI
services/orchestrator/   # Dagster assets (ingest → detect)
services/stream-worker/  # Kafka micro-batch consumer
infra/postgres/          # Database schema + migrations
config/                  # YAML sources, detectors, settings
docs/decisions/          # Architecture Decision Records
```

## Development Commands

| Command | Description |
|---------|-------------|
| `make install` | Sync dependencies with uv |
| `make repair-venv` | Kill locked `.venv` processes and reinstall |
| `make test` | Run pytest |
| `make lint` | Run ruff |
| `make typecheck` | Run mypy strict on core library |
| `make api` | FastAPI on port 8000 |
| `make dashboard` | Streamlit on port 8501 |
| `make worker` | ARQ worker for async alert notifications |
| `make orchestrator` | Dagster UI on port 3000 |
| `make docker-up` | Postgres (5433) + Redis + Redpanda |
| `make explain-demo` | Ingest + detect + explain sample CSV |
| `make mlops-demo` | Detect + MLflow tracking + run history |
| `make polish-demo` | Full demo path for Phase 10 validation |
| `make kafka-demo` | Redpanda publish + stream ingest + detect |

See `make help` for connector demos (NAB, Online Retail, Postgres poll).

## Phase Status (0 → 10)

| Phase | Scope | Status |
|-------|-------|--------|
| 0 | Foundations, Docker, CI | Done |
| 1 | CSV batch ingestion | Done |
| 2 | MAD + Isolation Forest detectors | Done |
| 3 | Synthetic benchmark (P/R/F1) | Done |
| 4 | Explainability (rules + attribution) | Done |
| 5 | API + Streamlit + ARQ alerting | Done |
| 6 | NAB, Online Retail, Postgres connectors | Done |
| 7 | Dagster orchestration | Done |
| 8 | Redpanda/Kafka streaming ingest | Done |
| 9 | MLflow tracking + Prometheus metrics | Done |
| 10 | Dashboard polish + readiness probes | Done |

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness (process up) |
| `GET /health/ready` | Readiness (Postgres + Redis) |
| `GET /metrics` | Prometheus scrape |
| `GET /streams` | Stream list with alert counts |
| `GET /streams/{name}/alerts` | Alert summaries |
| `GET /streams/{name}/runs` | Pipeline run history |
| `GET /alerts/{id}` | Alert detail + explanation |
| `POST /alerts/{id}/notify` | Webhook/Slack dispatch |

## Windows Notes

- Docker Postgres listens on **host port 5433** (not 5432) to avoid conflicts with a local PostgreSQL install.
- Dagster UI: use http://127.0.0.1:3000 (not `0.0.0.0`).
- If `uv sync` fails with file locks, run `make repair-venv` after stopping API/Dagster terminals.

## Documentation

- Architecture: `docs/architecture.md`
- Demo script: `docs/demo-script.md`
- ADRs: `docs/decisions/`

## License

MIT — see [LICENSE](LICENSE).
