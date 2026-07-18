# ADR 005: MLflow tracking + Prometheus metrics

## Status

Accepted (Phase 9)

## Context

Detection runs already persist scores and alerts in Postgres, but there is no experiment lineage or operational metrics for portfolio demos. Phase 9 requires lightweight MLOps and observability without a full model-serving stack.

## Decision

1. **MLflow** — log each `DetectService` run (params, metrics, detector YAML artifact) to a local SQLite store (`./mlruns/mlflow.db`).
2. **Run history API/CLI** — expose `GET /streams/{name}/runs` and `anomx runs --stream`.
3. **Prometheus** — expose `/metrics` on the FastAPI service with request counters and latency histogram.

## Consequences

- Reproducible detector configs and metrics visible in MLflow UI
- No sklearn model serialization in MVP (params/metrics only)
- SHAP deferred (Windows packaging issues from Phase 4)
- Production would use remote MLflow + Grafana dashboards + model registry promotion gates

**Interview one-liner:** *Postgres is the source of truth for alerts; MLflow adds experiment lineage and Prometheus adds SRE-style HTTP metrics — full model registry is the next step.*
