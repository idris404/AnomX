-- AnomX PostgreSQL schema (Phase 0)
-- Tables: streams, runs, observations, scores, alerts

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS streams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    config      JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS runs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id   UUID NOT NULL REFERENCES streams(id) ON DELETE CASCADE,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    metadata    JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_runs_stream_id ON runs(stream_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);

CREATE TABLE IF NOT EXISTS observations (
    id          BIGSERIAL PRIMARY KEY,
    run_id      UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    stream_id   UUID NOT NULL REFERENCES streams(id) ON DELETE CASCADE,
    observed_at TIMESTAMPTZ NOT NULL,
    payload     JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_observations_run_id ON observations(run_id);
CREATE INDEX IF NOT EXISTS idx_observations_stream_observed_at
    ON observations(stream_id, observed_at);

CREATE TABLE IF NOT EXISTS scores (
    id          BIGSERIAL PRIMARY KEY,
    run_id      UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    observation_id BIGINT NOT NULL REFERENCES observations(id) ON DELETE CASCADE,
    detector    TEXT NOT NULL,
    score       DOUBLE PRECISION NOT NULL,
    is_anomaly  BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scores_run_id ON scores(run_id);
CREATE INDEX IF NOT EXISTS idx_scores_observation_id ON scores(observation_id);

CREATE TABLE IF NOT EXISTS alerts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id      UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    stream_id   UUID NOT NULL REFERENCES streams(id) ON DELETE CASCADE,
    observation_id BIGINT REFERENCES observations(id) ON DELETE SET NULL,
    score       DOUBLE PRECISION NOT NULL,
    detector    TEXT NOT NULL,
    explanation JSONB NOT NULL DEFAULT '{}',
    dedupe_key  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alerts_stream_id ON alerts(stream_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_dedupe_key
    ON alerts(dedupe_key) WHERE dedupe_key IS NOT NULL;
