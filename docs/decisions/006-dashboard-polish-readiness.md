# ADR 006: Dashboard polish + production readiness probes

## Status

Accepted (Phase 10)

## Context

Phases 5 and 9 delivered a functional Streamlit dashboard (alerts only) and MLOps endpoints (`/streams/{name}/runs`, `/metrics`). Phase 10 closes the portfolio loop with operator-facing polish and minimal production hardening — without rewriting the UI in Next.js.

## Decision

1. **Streamlit dashboard tabs** — Overview (health + streams + metrics preview), Alerts (existing explainability panel), Runs (pipeline history + MLflow run IDs).
2. **Readiness probe** — `GET /health/ready` checks Postgres (`SELECT 1`) and Redis (`PING`); returns `503` when degraded. Keep `/health` as liveness-only.
3. **README + demo script** — document the full 0→10 journey and recruiter demo path.
4. **MIT license** — explicit open-source license for portfolio visibility.

## Consequences

- Kubernetes/Docker Compose can wire liveness vs readiness separately
- Dashboard surfaces run lineage without opening MLflow UI
- Next.js rewrite remains optional — Streamlit is sufficient for MVP demos
- Production would add auth (OAuth2/API keys), TLS termination, and Grafana dashboards wired to `/metrics`

**Interview one-liner:** *Liveness tells you the process is up; readiness tells you Postgres and Redis are actually reachable — the dashboard ties alerts, explanations, and run history into one operator view.*
