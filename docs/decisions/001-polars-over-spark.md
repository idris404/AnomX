# ADR 001: Polars over Spark

## Status

Accepted

## Context

AnomX needs fast batch data processing for CSV/Parquet ingestion. Spark is the default at scale but adds significant operational overhead for a solo portfolio project.

## Decision

Use **Polars** for ingestion and feature engineering (Phase 1+).

## Consequences

- Simpler local dev on Windows (no JVM cluster)
- Sufficient performance for MVP dataset sizes (NAB, Online Retail II)
- Migration to Spark/Dask remains possible via the `Source` protocol if volume demands it
