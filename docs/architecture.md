# AnomX Architecture

## Overview

AnomX is a pluggable anomaly detection engine. The codebase follows a strict **library vs. services** split:

- **`packages/anomx/`** — publishable Python library with zero web/orchestration dependencies
- **`services/api/`** — thin FastAPI layer that depends on `anomx`
- **`services/dashboard/`** — Streamlit UI
- **`services/orchestrator/`** — Dagster assets (Phase 7)

## Phase 5 (done)

API alert routes, Streamlit dashboard, webhook/Slack alerting, ARQ worker.

## Phase 6 Scope (current)

Additional connectors via `Source` protocol + `build_source()` factory:

| Flux | Connector | `source_type` | Purpose |
|------|-----------|---------------|---------|
| A | `NabBatchSource` | `nab_batch` | NAB labeled CSV + anomaly windows in payload |
| B | `OnlineRetailBatchSource` | `online_retail_batch` | Daily revenue/quantity aggregation |
| C | `PostgresQuerySource` | `postgres_query` | SQL snapshot poll (Pagila-style queries) |

CLI unchanged: `anomx ingest --config config/sources/<source>.yaml`

**Compromis MVP** :
- NAB labels from `combined_windows.json` (not full NAB eval pipeline)
- Online Retail = synthetic sample script (full UCI file optional offline)
- Pagila = generic SQL query; demo uses AnomX Postgres replay unless Pagila DB is loaded

## Phase 7 Scope (next)

Dagster orchestration assets.

## Data Flow

```
Connectors → Ingestion → Detection → Scoring → Storage → API / Dashboard / Alerting
                                              ↘ Explain (on alert)
                                                              ↘ ARQ notify
```

See `docs/decisions/` for Architecture Decision Records.
