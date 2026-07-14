# AnomX Architecture

## Overview

AnomX is a pluggable anomaly detection engine. The codebase follows a strict **library vs. services** split:

- **`packages/anomx/`** — publishable Python library with zero web/orchestration dependencies
- **`services/api/`** — thin FastAPI layer that depends on `anomx`
- **`services/dashboard/`** — Streamlit UI (Phase 5)
- **`services/orchestrator/`** — Dagster assets (Phase 7)

## Phase 0–4 (done)

See git history / prior docs for ingestion, detection, benchmark, and explainability scopes.

## Phase 5 Scope (current)

API + dashboard MVP + async alerting:

- **FastAPI routes** — `GET /streams`, `GET /streams/{name}/alerts`, `GET /alerts/{id}`, `POST /alerts/{id}/notify`
- **`AlertService`** — read-side queries with full explanation payloads
- **`AlertingService`** — webhook + Slack incoming webhook alerters
- **ARQ worker** — async notification dispatch via Redis (already in Docker Compose)
- **Streamlit dashboard** — alert table + **"Why this alert?"** panel (summary, rules, contributions, per-detector breakdown)

**Compromis MVP** : dashboard consomme l'API REST (pas de WebSocket live) ; alerting activé via `config/settings.yaml` ; pas de RBAC/auth sur l'API.

## Phase 6 Scope (next)

Additional connectors (NAB, Online Retail II), Pagila poll source.

## Data Flow (target)

```
Connectors → Ingestion → Detection → Scoring → Storage → API / Dashboard / Alerting
                                              ↘ Explain (on alert)
                                                              ↘ ARQ notify
```

See `docs/decisions/` for Architecture Decision Records.
