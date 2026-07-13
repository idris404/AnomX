-- Phase 1 migration: idempotent ingestion support
-- Run manually on existing databases created before Phase 1:
--   docker exec -i anomx-postgres psql -U anomx -d anomx < infra/postgres/migrations/001_phase1_ingestion.sql

ALTER TABLE observations
    ADD COLUMN IF NOT EXISTS row_fingerprint TEXT;

UPDATE observations
SET row_fingerprint = md5(stream_id::text || observed_at::text || payload::text)
WHERE row_fingerprint IS NULL;

ALTER TABLE observations
    ALTER COLUMN row_fingerprint SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_observations_stream_row_fingerprint
    ON observations(stream_id, row_fingerprint);

CREATE UNIQUE INDEX IF NOT EXISTS idx_runs_stream_content_hash
    ON runs(stream_id, (metadata->>'content_hash'))
    WHERE status = 'completed' AND metadata->>'content_hash' IS NOT NULL;
