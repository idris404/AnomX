# AnomX Architecture

## Overview

AnomX is a pluggable anomaly detection engine. The codebase follows a strict **library vs. services** split:

- **`packages/anomx/`** — publishable Python library (no Dagster/FastAPI/Streamlit)
- **`services/api/`** — FastAPI + ARQ workers
- **`services/dashboard/`** — Streamlit UI
- **`services/orchestrator/`** — Dagster assets (Phase 7)

## Phase 7 Scope (current)

Dagster asset-centric orchestration (ADR 002):

| Asset | Wraps | Output |
|-------|-------|--------|
| `ingestion_run` | `IngestService.ingest()` | observations in Postgres |
| `detection_run` | `DetectService.detect_stream()` | scores + alerts + explanations |

**Jobs:** `stream_pipeline`, `sample_csv_pipeline`, `nab_pipeline`

**Compromis MVP:** materialisation manuelle via UI/CLI — pas de sensors/schedules, pas de Dagster dans Docker Compose.

## Phase 8 Scope (current)

Event-driven ingestion via Redpanda/Kafka (ADR 004):

| Component | Role |
|-----------|------|
| `KafkaJsonSource` | Micro-batch consumer (JSON observations) |
| `StreamIngestService` | Persist micro-batch → Postgres |
| `services/stream-worker/` | CLI consumer loop |
| `scripts/publish_sample_to_kafka.py` | Demo producer (replays sample CSV) |

**Compromis MVP:** micro-batch CLI, pas Debezium ni exactly-once — remplace le poll SQL Phase 6 pour Flux C.

## Phase 9 Scope (done)

MLOps + observability (ADR 005):

| Component | Role |
|-----------|------|
| `MlflowDetectTracker` | Log detect params/metrics to `./mlruns` |
| `RunService` | Pipeline run history (ingest + detect) |
| `GET /streams/{name}/runs` | Operational visibility |
| `GET /metrics` | Prometheus scrape endpoint |

**Compromis MVP:** SQLite MLflow, pas de model registry ni Grafana — suffisant pour démo portfolio.

## Phase 10 Scope (current)

Dashboard polish + production hardening (ADR 006):

| Component | Role |
|-----------|------|
| Streamlit tabs | Overview (health, streams), Alerts, Runs |
| `GET /health/ready` | Postgres + Redis readiness probe |
| `GET /health` | Liveness only (unchanged) |
| README + LICENSE | Portfolio-ready documentation |

**Compromis MVP:** Streamlit (not Next.js), no auth/TLS — readiness probes are the production hook for K8s.

## Data Flow

```
Connectors → [ingestion_run] → observations → [detection_run] → scores/alerts
                                              ↘ Explain (inline)
Storage → API / Dashboard / ARQ notify
```

See `docs/decisions/` for Architecture Decision Records.
