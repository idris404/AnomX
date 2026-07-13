# Demo Script (Phase 5+)

This document will contain the 10-minute recruiter demo script once the MVP is complete.

## Phase 0 Validation Checklist

```powershell
uv sync --all-packages --dev
docker compose up -d
make test
make api
# In another terminal:
curl http://localhost:8000/health
```

Expected health response:

```json
{"status":"ok","service":"anomx-api","version":"0.1.0"}
```
