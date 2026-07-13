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

## Phase 1 Scope

- `CsvBatchSource` — Polars read + Pandera validation
- Postgres persistence via `runs` + `observations` (maps to ingestion_runs / raw_events)
- CLI `anomx ingest --config config/sources/<source>.yaml`
- Idempotent re-ingestion via file content hash

## Phase 2 Scope

- `MADDetector` — robust univariate baseline (MAD z-score)
- `IsolationForestDetector` — multivariate sklearn baseline
- `EnsembleDetector` — weighted fusion + percentile calibration
- CLI `anomx detect --stream <name>`
- Persistence in `scores` and `alerts` tables

## Phase 3 Scope

- `AnomalyInjector` — point, contextual, drift anomalies (seed fixe)
- `BenchmarkRunner` — évaluation solo + ensemble, protocole reproductible
- Métriques : precision, recall, F1, FP/h, latence fit/predict
- CLI `anomx benchmark --config config/benchmark.yaml`
- Rapports auto-générés dans `reports/` (JSON + Markdown)

**Compromis MVP** : métriques point-level (pas de fenêtre de tolérance event-level NAB). MAD performe mal sur drift/contextual — c'est documenté honnêtement dans le rapport.

## Phase 4 Scope (current)

Human-defensible alert explanations stored in `alerts.explanation` JSONB:

- **`explain/mad_rules.py`** — rule-based MAD explanations (median, MAD, robust z, threshold)
- **`explain/if_attribution.py`** — permutation-based feature attribution for Isolation Forest
- **`explain/builder.py`** — composite ensemble explanation (summary, rules, per-detector contributions)
- **`ExplainService`** + CLI `anomx explain --stream <name> --limit N`
- Integrated into `DetectService` at alert creation time

**Compromis MVP** : pas de SHAP (packaging Windows/Python 3.11 fragile) — attribution par permutation vs médianes de la fenêtre de fit, output compatible avec le panneau UI Phase 5. Pas de résumé LLM.

## Phase 5 Scope (next)

FastAPI routes for alerts, Streamlit dashboard with "Why this alert?" panel, webhook/Slack alerting, ARQ async jobs.

## Data Flow (target)

```
Connectors → Ingestion → Detection → Scoring → Storage → API / Dashboard / Alerting
                                              ↘ Explain (on alert)
```

See `docs/decisions/` for Architecture Decision Records.
