# ADR 002: Dagster asset-centric orchestration

## Status

Accepted (Phase 7)

## Context

Pipeline steps (raw → features → scores → alerts) produce auditable data artifacts. Task-centric orchestrators (Airflow, Prefect) model workflows as DAGs of tasks.

## Decision

Use **Dagster** with asset-centric modeling when orchestration is added in Phase 7.

## Consequences

- Each pipeline stage is a versioned, observable asset
- Stronger data engineering narrative for portfolio
- Steeper learning curve than Prefect (~1 week budget assumed)
