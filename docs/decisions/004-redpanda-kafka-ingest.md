# ADR 004: Redpanda + Kafka JSON ingest

## Status

Accepted (Phase 8)

## Context

Phase 6 proved the observation schema with SQL snapshots (Flux C stand-in). Production event-driven pipelines use Kafka-compatible brokers and CDC (Debezium). AnomX needs a streaming transport without rewriting detect/explain/API layers.

## Decision

Use **Redpanda** (single-node, Docker) and **aiokafka** with JSON messages on topic `anomx.observations`. A thin `services/stream-worker` consumes micro-batches into the same Postgres `observations` table, then optionally calls existing `DetectService`.

## Consequences

- Same downstream pipeline (detect, explain, API, dashboard) for batch and stream
- MVP avoids Schema Registry, Debezium, and exactly-once semantics
- Production path: Debezium CDC from Pagila → Kafka → same consumer contract
- Dagster remains batch-oriented in MVP; stream worker runs independently

## MVP vs production

| MVP (Phase 8) | Production |
|---------------|------------|
| Redpanda dev-container | Managed Kafka / Redpanda cluster |
| JSON payloads | Avro/Protobuf + Schema Registry |
| Micro-batch consumer CLI | Long-running consumer + lag metrics |
| Manual `make kafka-demo` | Debezium Connect, sensors, alerting on lag |
| Offset in run metadata | Dedicated offset store + replay tooling |

**Interview one-liner:** *Phase 6 validated the schema with SQL snapshots; Phase 8 swaps transport to Kafka-compatible events while keeping Postgres + detect — Debezium CDC is the production upgrade for Flux C.*
