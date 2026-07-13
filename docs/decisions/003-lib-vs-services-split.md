# ADR 003: Library vs. services split

## Status

Accepted

## Context

AnomX needs to be both a reusable Python package (`pip install anomx`) and a deployable product (API, dashboard, orchestrator).

## Decision

Separate **`packages/anomx/`** (pure library) from **`services/*`** (application layers). The library must never import FastAPI, Streamlit, or Dagster.

## Consequences

- Clean packaging story for PyPI (Phase 10)
- Services remain thin wrappers — no duplicated business logic
- Clear interview narrative: "separation of concerns between engine and delivery"
