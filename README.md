# AnomX

**Anomaly detection you can actually run end-to-end** — ingest time series, score them with pluggable detectors, explain the alerts, and expose everything through a CLI, REST API, and operator dashboard.

Batch and streaming pipelines, Postgres storage, Dagster orchestration, MLflow experiment tracking, and Prometheus metrics.

[![CI](https://github.com/idris404/AnomX/actions/workflows/ci.yml/badge.svg)](https://github.com/idris404/AnomX/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What it does

AnomX ingests observations (CSV, NAB benchmarks, Kafka JSON, Postgres polls), runs an ensemble of detectors, and stores scores + alerts in PostgreSQL. When something looks off, you get a human-readable explanation — MAD z-score rules for statistical spikes, permutation attribution for Isolation Forest.

The same core library powers everything:

```
Sources          Ingest              Detect              Output
────────         ──────              ──────              ──────
CSV / NAB   →    validate +     →    MAD + IF       →    alerts + explanations
Kafka JSON       dedupe               ensemble             REST API
Postgres poll                         calibration          Streamlit dashboard
                                                           webhook / Slack (ARQ)
```

**Detectors shipped today:** Median Absolute Deviation (MAD) and Isolation Forest, combined with weighted ensemble scoring and percentile calibration. Synthetic benchmark included (precision / recall / F1, false positives per hour).

**What this is not:** a managed SaaS, a model registry, or a replacement for Datadog. It's a reference implementation you can fork, extend with your own connectors, and defend in a technical interview.

---

## Requirements

| Tool | Version | Why |
|------|---------|-----|
| [Python](https://www.python.org/downloads/) | 3.11.x | Pinned in `.python-version` — 3.12+ is not supported |
| [uv](https://docs.astral.sh/uv/) | latest | Dependency and workspace management |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | latest | PostgreSQL 16, Redis 7, Redpanda (Kafka-compatible) |
| GNU Make | any | Task runner — on Windows, install via [GnuWin32](https://gnuwin32.sourceforge.net/packages/make.htm) or `winget install GnuWin32.Make` |

Development is tested on **Windows + PowerShell**. Linux and macOS work with the same commands if `make`, `docker`, and `uv` are on your PATH.

---

## Installation

```powershell
git clone https://github.com/idris404/AnomX.git
cd AnomX

make install      # uv sync — creates .venv and installs all workspace packages
make docker-up    # Postgres :5433, Redis :6379, Redpanda :19092
make test         # 53 tests (integration tests skip if Postgres is down)
```

If `uv sync` fails with file-lock errors on Windows, stop any running `make api` / `make orchestrator` terminals, then:

```powershell
make repair-venv
```

---

## Quick start (5 minutes)

Seed data, run detection, open the dashboard:

```powershell
make polish-demo     # ingest → detect → MLflow log → print run history
```

**Terminal 1 — API**

```powershell
make api
# http://127.0.0.1:8000/docs
```

**Terminal 2 — Dashboard**

```powershell
make dashboard
# http://127.0.0.1:8501
```

The dashboard has three tabs: **Overview** (health checks, stream list), **Alerts** (scores + explanations), **Runs** (ingestion and detection history, including MLflow run IDs).

Verify the API:

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/ready
curl http://127.0.0.1:8000/streams/sample_csv/alerts
```

`/health` is liveness (process up). `/health/ready` checks Postgres and Redis — returns `503` if Docker isn't running.

---

## CLI

All pipeline steps are available through the `anomx` command (installed via the workspace venv):

```powershell
# Ingest a configured source
uv run anomx ingest --config config/sources/sample_csv.yaml

# Run detection on an ingested stream
uv run anomx detect --stream sample_csv --config config/detectors.yaml

# Show explanations for recent alerts
uv run anomx explain --stream sample_csv --limit 5

# Pipeline run history
uv run anomx runs --stream sample_csv --limit 10

# Reproducible detector benchmark (writes reports/*.json and *.md)
uv run anomx benchmark --config config/benchmark.yaml
```

Re-running ingest on the same file is idempotent (content hash dedupe). Re-running detect upserts alerts and refreshes explanations.

### Source configs

| Config | Stream name | Description |
|--------|-------------|-------------|
| `config/sources/sample_csv.yaml` | `sample_csv` | Generated 100-row CSV (default demo) |
| `config/sources/nab_cpu_utilization.yaml` | `nab_cpu_utilization` | NAB benchmark slice (labeled) |
| `config/sources/online_retail_daily.yaml` | `online_retail_daily` | Online Retail II daily aggregate |
| `config/sources/postgres_observations_hourly.yaml` | `postgres_observations_hourly` | SQL poll against local Postgres |
| `configs/streams/kafka_sample.yaml` | `kafka_sample` | Kafka JSON micro-batch (see below) |

Detector ensemble is configured in `config/detectors.yaml`. Database connection lives in `config/settings.yaml` (default port **5433**).

---

## Make targets

Run `make help` for the full list. Common targets grouped by purpose:

**Infrastructure**

| Command | Description |
|---------|-------------|
| `make docker-up` | Start Postgres, Redis, Redpanda |
| `make docker-down` | Stop containers |
| `make db-reset` | Wipe volumes and recreate |

**Services** (each in its own terminal)

| Command | URL |
|---------|-----|
| `make api` | http://127.0.0.1:8000 |
| `make dashboard` | http://127.0.0.1:8501 |
| `make orchestrator` | http://127.0.0.1:3000 (Dagster — use `127.0.0.1`, not `0.0.0.0`) |
| `make worker` | ARQ worker for async alert notifications |

**Demos**

| Command | What it runs |
|---------|--------------|
| `make explain-demo` | sample CSV → ingest → detect → explain |
| `make nab-demo` | Download NAB sample → ingest → detect |
| `make retail-demo` | Generate retail data → ingest → detect |
| `make kafka-demo` | Publish to Redpanda → stream worker → detect |
| `make orchestrator-demo` | Headless Dagster job (`sample_csv_pipeline`) |
| `make mlops-demo` | Detect + MLflow tracking + run history |
| `make polish-demo` | Full Phase 10 validation path |

**Quality**

| Command | Description |
|---------|-------------|
| `make test` | pytest across all packages |
| `make lint` | ruff |
| `make typecheck` | mypy strict on `packages/anomx/anomx` |

---

## REST API

Interactive docs at http://127.0.0.1:8000/docs when the API is running.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe |
| `GET` | `/health/ready` | Readiness — Postgres + Redis |
| `GET` | `/metrics` | Prometheus exposition format |
| `GET` | `/streams` | All streams with alert counts |
| `GET` | `/streams/{name}/alerts` | Alert summaries for a stream |
| `GET` | `/streams/{name}/runs` | Ingestion + detection run history |
| `GET` | `/alerts/{id}` | Full alert detail with explanation |
| `POST` | `/alerts/{id}/notify` | Queue or send webhook/Slack alert |

Alerting channels are configured in `config/settings.yaml` (`alerting.webhook`, `alerting.slack`). Async dispatch requires `make worker` and Redis.

---

## Streaming (Kafka / Redpanda)

Phase 8 adds event-driven ingestion alongside batch:

```powershell
make docker-up
make kafka-demo
```

This publishes sample observations to topic `anomx.observations` on `127.0.0.1:19092`, consumes a micro-batch via `services/stream-worker/`, and runs detection. MVP uses a CLI consumer loop — production would use Debezium CDC and consumer groups with offset management.

---

## MLflow & observability

Each `anomx detect` run logs parameters and metrics to a local SQLite store (`./mlruns/mlflow.db`) when enabled in `config/settings.yaml`.

Optional UI (requires the full `mlflow` package, not just `mlflow-skinny`):

```powershell
uv pip install mlflow
uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
```

Prometheus metrics are exposed at `/metrics` on the API service (HTTP request counts and latency histograms).

---

## Repository layout

```
AnomX/
├── packages/anomx/           Core library — connectors, detectors, CLI (pip-installable)
├── services/
│   ├── api/                  FastAPI + ARQ workers
│   ├── dashboard/            Streamlit operator UI
│   ├── orchestrator/         Dagster assets (ingest → detect jobs)
│   └── stream-worker/        Kafka micro-batch consumer
├── config/                   Source YAML, detector config, settings
├── configs/streams/          Kafka stream definitions
├── infra/postgres/           Schema + migrations
├── scripts/                  Sample data generators, Kafka producer
├── docs/
│   ├── architecture.md       System overview
│   ├── demo-script.md        Step-by-step validation checklists
│   └── decisions/            Architecture Decision Records (ADRs)
├── Makefile                  All commands above
└── docker-compose.yml        Postgres, Redis, Redpanda
```

The split between `packages/anomx/` (pure Python, no FastAPI/Dagster) and `services/*` (thin deployment layers) is intentional — see [ADR 003](docs/decisions/003-lib-vs-services-split.md).

---

## Contributing

Issues and pull requests are welcome. A few conventions to keep the codebase consistent:

1. **Python 3.11 only** — no 3.12 syntax or dependencies.
2. **Run checks before opening a PR:**
   ```powershell
   make lint
   make typecheck
   make test
   ```
3. **Scope new features to the right layer:**
   - Connectors and detectors → `packages/anomx/anomx/`
   - HTTP routes → `services/api/app/routes/`
   - Stream configs → `config/sources/` or `configs/streams/`
4. **Add or update tests** when changing behaviour. Integration tests that need Postgres are marked `@pytest.mark.integration` and skip gracefully when Docker isn't up.
5. **Document non-obvious trade-offs** — if you simplify for MVP, add a note to `docs/decisions/` or the relevant ADR.

For a guided walkthrough of every pipeline stage, see [`docs/demo-script.md`](docs/demo-script.md).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `password authentication failed` on ingest | Another Postgres may be bound to port 5433. Check `config/settings.yaml` uses `port: 5433` and run `make docker-up`. |
| `uv sync` / file lock on Windows | Stop API and Dagster terminals, then `make repair-venv`. |
| Dagster UI won't load | Use http://127.0.0.1:3000. First load can take ~15 s. Keep the terminal open. |
| `/health/ready` returns 503 | Docker not running or containers still starting. Wait for `docker compose ps` to show healthy. |
| Dashboard `ModuleNotFoundError` | Run via `make dashboard` from the repo root (not `streamlit run` manually from another cwd). |
| Integration tests skipped | Expected without Postgres. Start Docker and re-run `make test`. |

---

## License

MIT — see [LICENSE](LICENSE).
