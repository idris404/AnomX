# AnomX Architecture

## Overview

AnomX is a pluggable anomaly detection engine. The codebase follows a strict **library vs. services** split:

- **`packages/anomx/`** — publishable Python library with zero web/orchestration dependencies
- **`services/api/`** — thin FastAPI layer that depends on `anomx`
- **`services/dashboard/`** — Streamlit UI (Phase 5)
- **`services/orchestrator/`** — Dagster assets (Phase 7)

## Phase 0 Scope

Phase 0 established foundations only:

- Protocol interfaces (`Source`, `Sink`, `Detector`, `Alerter`)
- PostgreSQL schema (streams, runs, observations, scores, alerts)
- Docker Compose (PostgreSQL 16 + Redis 7)
- FastAPI health endpoint
- CI pipeline (ruff + mypy strict + pytest)

## Phase 1 Scope (current)

- `CsvBatchSource` — Polars read + Pandera validation
- Postgres persistence via `runs` + `observations` (maps to ingestion_runs / raw_events)
- CLI `anomx ingest --config config/sources/<source>.yaml`
- Idempotent re-ingestion via file content hash

No detection logic or orchestration yet.

## Data Flow (target)

```
Connectors → Ingestion → Detection → Scoring → Storage → API / Dashboard / Alerting
```

See `docs/decisions/` for Architecture Decision Records.
