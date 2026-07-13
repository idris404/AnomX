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
