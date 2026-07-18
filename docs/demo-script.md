# Demo Script (Phase 5+)

This document will contain the 10-minute recruiter demo script once the MVP is complete.

## Phase 1 Validation Checklist

```powershell
make install
make docker-up
make test                 # 11 tests including 10k-row integration
make sample-data
make ingest-demo          # first run: 100 rows written
make ingest-demo          # second run: skipped=true (idempotent)
```

Expected ingest output (first run):

```json
{"records_read": 100, "records_written": 100, "skipped": false}
```

Expected ingest output (second run):

```json
{"records_read": 100, "records_written": 0, "skipped": true}
```

## Phase 3 Validation Checklist

```powershell
make benchmark
# attendu : reports/benchmark_*.json + reports/benchmark_*.md

# Re-run identique → mêmes métriques P/R/F1 (latence peut varier)
make benchmark
```

Inspect the Markdown report for detector comparison. Mixed anomaly types (point + contextual + drift) intentionally stress-test detector limits — MAD recall will be lower than on point-only spikes.

## Phase 4 Validation Checklist

```powershell
make explain-demo
# attendu : JSON avec summary, rules (median/MAD/z-score), feature_contributions

uv run anomx explain --stream sample_csv --limit 3
```

Expected explain output fields:

- `summary` — one-line ensemble + primary detector reason
- `rules` — MAD rules + IF permutation attribution lines
- `feature_contributions` — weighted feature drivers (e.g. `value`)

Re-run `make detect-demo` on an existing stream updates explanations in place (alert dedupe upsert).

## Phase 5 Validation Checklist

Prerequisite (once per env change):

```powershell
make install
```

Terminal 1:

```powershell
make docker-up
make explain-demo
make api
```

Terminal 2 (while API is running — use `--no-sync` via Makefile to avoid Windows file locks on `anomx.exe`):

```powershell
make dashboard
```

Open http://localhost:8501 in the browser.

Optional async alerting (requires webhook/Slack enabled in `config/settings.yaml`):

```powershell
make worker
curl -X POST "http://localhost:8000/alerts/<alert_id>/notify?async=true"
```

Expected:
- API returns alerts with `summary`, `rules`, `feature_contributions`
- Dashboard shows alert table + "Why this alert?" detail panel
- Worker logs `notify_alert_complete` when alerters are enabled

## Phase 6 Validation Checklist

```powershell
make nab-data
make nab-demo
# attendu : stream nab_cpu_utilization ingéré + detect

make retail-data
make retail-demo
# attendu : stream online_retail_daily (120 jours agrégés)

make explain-demo
make postgres-demo
# attendu : stream postgres_observations_hourly (~200 points replay depuis sample_csv)
```

Inspect payloads in Postgres — NAB rows should include `label` and `dataset` in `observations.payload`.

## Phase 7 Validation Checklist

Terminal 1:

```powershell
make docker-up
make orchestrator
```

Open http://127.0.0.1:3000 — materialize `sample_csv_pipeline` or assets `ingestion_run` → `detection_run`.

> **Windows:** n'utilise pas `http://0.0.0.0:3000` dans le navigateur — ça ne marche pas. Garde le terminal `make orchestrator` ouvert (le serveur tourne en foreground). Le premier chargement peut prendre ~15–20 s.

Terminal 2 (headless):

```powershell
make orchestrator-demo
# attendu : job sample_csv_pipeline SUCCESS, same effect as make detect-demo
```

Verify in Postgres or CLI:

```powershell
uv run anomx explain --stream sample_csv --limit 3
```

## Phase 8 Validation Checklist

```powershell
make docker-up
make kafka-demo
# attendu : 200 messages published, stream worker ingests + detect, explain JSON
```

Re-run with a fresh consumer group if the topic was already consumed:

```powershell
uv run python scripts/publish_sample_to_kafka.py
uv run --directory services/stream-worker python -m anomx_stream_worker.main --detect --group-id anomx-demo-v2
uv run anomx explain --stream kafka_sample --limit 3
```

Redpanda UI/console: broker on `127.0.0.1:19092`. MVP uses JSON on topic `anomx.observations` — Debezium CDC is the production path for Flux C (Pagila).
