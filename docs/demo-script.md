# Recruiter demo (local reference implementation)

Run these commands from the repository root with Python 3.11, uv, Docker, and Make installed. PostgreSQL uses host port 5433; Redpanda uses 19092. Compose binds both to `127.0.0.1`; its credentials are only for local development. This demo needs PostgreSQL; Redpanda is needed only for the optional Kafka step.

## Five-minute path

```sh
make install
make docker-up
docker compose ps                 # wait for PostgreSQL to be healthy
make sample-data                 # 200 rows, including 10 injected spikes
uv run anomx ingest --config config/sources/sample_csv.yaml
uv run anomx ingest --config config/sources/sample_csv.yaml
uv run anomx detect --stream sample_csv --config config/detectors.yaml
uv run anomx explain --stream sample_csv --limit 1
uv run anomx runs --stream sample_csv --limit 3
```

The first ingestion reports `records_read: 200`, `records_written: 200`, `skipped: false` on a fresh database. The second reports `records_written: 0`, `skipped: true` with the same run ID. Detection scores 200 observations and creates alerts on a fresh database. The exact number of alerts depends on the detector implementation and data. The explanation includes the ensemble score and threshold, MAD rule, Isolation Forest attribution, and a primary signal based on each detector's weighted normalized contribution. Rerunning detection updates existing alerts, so `alerts_created` can be 0 while the alerts remain available.

In a second terminal:

```sh
make api
```

Then check the actual data and API telemetry:

```sh
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/streams/sample_csv/alerts
curl http://127.0.0.1:8000/streams/sample_csv/runs
curl http://127.0.0.1:8000/metrics
```

`/health` proves only that the API process is running. `/metrics` exposes HTTP request counts and latency, not model quality. `anomx detect` also writes local MLflow run parameters, counts, and the detector config artifact to `mlruns/mlflow.db` when enabled. Open the dashboard in a third terminal with `make dashboard`, then visit http://127.0.0.1:8501 and select `sample_csv` to inspect an alert. The dashboard reads the API; it does not show run history or MLflow charts.

## Optional source and orchestration checks

```sh
make nab-demo             # downloads NAB data; network required
make postgres-demo        # polls a PostgreSQL aggregate
make kafka-demo           # publishes and consumes one bounded Kafka micro-batch
make orchestrator-demo    # materializes the sample CSV Dagster job
make test                 # includes marked PostgreSQL and Kafka integration tests
```

The Kafka worker consumes one bounded batch and exits. It is suitable for demonstrating transport and storage, not continuous production streaming. The PostgreSQL poll is a snapshot query, not change data capture. External NAB download and Dagster CLI execution are optional steps; the automated suite covers the NAB connector and Dagster asset definitions, while the full Docker run covers Kafka and PostgreSQL ingestion.

If port 5433 is occupied by another project, leave that service alone. Map AnomX PostgreSQL to a free host port and set `ANOMX_POSTGRES_PORT` to that port for CLI, API, and tests. The standard `make docker-up` target itself expects port 5433.
