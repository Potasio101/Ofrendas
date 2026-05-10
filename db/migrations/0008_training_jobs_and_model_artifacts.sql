-- 0008_training_jobs_and_model_artifacts.sql
-- Adds async training job state tracking and model artifact metadata.

BEGIN;

CREATE TABLE IF NOT EXISTS training_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_type TEXT NOT NULL CHECK (trigger_type IN ('force', 'scheduled', 'retry')),
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'canceled')),
    requested_by_user_id UUID REFERENCES users(id),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    failure_reason TEXT,
    trace_ref TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS training_model_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    training_job_id UUID NOT NULL REFERENCES training_jobs(id) ON DELETE CASCADE,
    artifact_version TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    dataset_hash TEXT NOT NULL,
    train_size INTEGER NOT NULL DEFAULT 0,
    validation_size INTEGER NOT NULL DEFAULT 0,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_training_jobs_status_created ON training_jobs(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_training_jobs_created ON training_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_training_model_artifacts_created ON training_model_artifacts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_training_model_artifacts_job ON training_model_artifacts(training_job_id);

COMMIT;
