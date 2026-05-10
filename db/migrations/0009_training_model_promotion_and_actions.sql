-- 0009_training_model_promotion_and_actions.sql
-- Adds model registry status and promotion/rollback action logging.

BEGIN;

ALTER TABLE training_model_artifacts
    ADD COLUMN IF NOT EXISTS model_status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (model_status IN ('candidate', 'active', 'archived', 'failed')),
    ADD COLUMN IF NOT EXISTS promoted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS promoted_by_user_id UUID REFERENCES users(id);

CREATE INDEX IF NOT EXISTS idx_training_model_artifacts_status_created
    ON training_model_artifacts(model_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_training_model_artifacts_status_promoted
    ON training_model_artifacts(model_status, promoted_at DESC);

CREATE TABLE IF NOT EXISTS training_model_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_type TEXT NOT NULL CHECK (action_type IN ('force', 'scheduled', 'promote', 'rollback')),
    actor_user_id UUID REFERENCES users(id),
    artifact_id UUID REFERENCES training_model_artifacts(id) ON DELETE SET NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_training_model_actions_created
    ON training_model_actions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_training_model_actions_type_created
    ON training_model_actions(action_type, created_at DESC);

COMMIT;
