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
