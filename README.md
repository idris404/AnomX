# AnomX

Pluggable anomaly detection engine for time series and tabular data.

## Prerequisites (Windows)

Install these tools and ensure they are on your PATH:

1. **Python 3.11** — pinned via `.python-version`
2. **[uv](https://docs.astral.sh/uv/)** — dependency manager
3. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** — PostgreSQL + Redis
4. **GNU Make** — via GnuWin32:
   ```powershell
   winget install GnuWin32.Make
   ```
   Restart PowerShell after installation so `make` is recognized.

## Quick Start

```powershell
# Clone and enter the repo
cd AnomX

# Install all workspace dependencies
make install

# Start infrastructure (PostgreSQL 16 + Redis 7)
make docker-up

# Run tests
make test

# Start the API (port 8000)
make api
```

In a second terminal:

```powershell
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","service":"anomx-api","version":"0.1.0"}
```

## Project Structure

```
packages/anomx/     # Core library (publishable, no web deps)
services/api/       # FastAPI REST service
infra/postgres/     # Database schema
config/             # YAML configuration (Phase 1+)
docs/               # Architecture docs and ADRs
```

## Development Commands

| Command         | Description                          |
|-----------------|--------------------------------------|
| `make install`  | Sync dependencies with uv            |
| `make test`     | Run pytest                           |
| `make lint`     | Run ruff                             |
| `make typecheck`| Run mypy strict on core library      |
| `make api`      | Start FastAPI dev server             |
| `make docker-up`| Start Postgres + Redis               |
| `make docker-down`| Stop containers                    |

## Phase 0 Status

This is the **Phase 0 foundation** — interfaces, schema, health API, CI. Detection, ingestion, benchmark, and dashboard arrive in subsequent phases.

## License

MIT (to be added in Phase 10)
