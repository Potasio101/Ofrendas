-- 0002_audit_and_exports.sql
-- Adds export run tracking and generic audit trail.

BEGIN;

CREATE TABLE IF NOT EXISTS export_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL CHECK (provider IN ('quickbooks_online', 'quickbooks_desktop', 'xero', 'zoho_books', 'sage', 'generic_csv')),
    export_format TEXT NOT NULL CHECK (export_format IN ('csv', 'iif', 'json')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    destination_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'running', 'success', 'failed')),
    total_rows INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    triggered_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS export_run_items (
    export_run_id UUID NOT NULL REFERENCES export_runs(id) ON DELETE CASCADE,
    offering_id UUID NOT NULL REFERENCES offerings(id) ON DELETE RESTRICT,
    PRIMARY KEY (export_run_id, offering_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    actor_user_id UUID REFERENCES users(id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_export_runs_provider_period ON export_runs(provider, period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_export_runs_status_created_at ON export_runs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor_created_at ON audit_log(actor_user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);

COMMIT;
