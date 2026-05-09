-- 0004_review_queue_and_field_history.sql
-- Adds deferred review workflow and field-level audit history.

BEGIN;

ALTER TABLE offerings
ADD COLUMN IF NOT EXISTS review_status TEXT NOT NULL DEFAULT 'pending_review'
CHECK (review_status IN ('pending_review', 'reviewed', 'needs_followup', 'closed'));

ALTER TABLE offerings
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

ALTER TABLE offerings
ADD COLUMN IF NOT EXISTS reviewed_by_user_id UUID REFERENCES users(id);

CREATE TABLE IF NOT EXISTS review_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    offering_id UUID NOT NULL UNIQUE REFERENCES offerings(id) ON DELETE CASCADE,
    queue_status TEXT NOT NULL DEFAULT 'open' CHECK (queue_status IN ('open', 'in_progress', 'resolved', 'escalated')),
    priority SMALLINT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    assigned_to_user_id UUID REFERENCES users(id),
    opened_by_user_id UUID REFERENCES users(id),
    reason TEXT,
    due_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS offering_field_history (
    id BIGSERIAL PRIMARY KEY,
    offering_id UUID NOT NULL REFERENCES offerings(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_type TEXT NOT NULL CHECK (change_type IN ('ocr_capture', 'initial_confirm', 'deferred_correction', 'admin_adjustment')),
    changed_by_user_id UUID REFERENCES users(id),
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_offerings_review_status_date ON offerings(review_status, service_date);
CREATE INDEX IF NOT EXISTS idx_review_queue_status_priority ON review_queue(queue_status, priority);
CREATE INDEX IF NOT EXISTS idx_review_queue_assigned_status ON review_queue(assigned_to_user_id, queue_status);
CREATE INDEX IF NOT EXISTS idx_offering_field_history_offering_time ON offering_field_history(offering_id, created_at);

COMMIT;
