-- 0007_outputs_and_disbursements.sql
-- Adds output/disbursement tracking with configurable fund source and approvals.

BEGIN;

CREATE TABLE IF NOT EXISTS fund_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_code TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    requires_extra_justification BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO fund_sources (source_code, source_name, is_active, requires_extra_justification)
VALUES
    ('offering', 'Offering', TRUE, FALSE),
    ('tithe', 'Tithe', TRUE, TRUE),
    ('other', 'Other', TRUE, FALSE)
ON CONFLICT (source_code) DO NOTHING;

CREATE TABLE IF NOT EXISTS disbursements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    output_date DATE NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('operational', 'benevolence', 'reimbursement', 'other')),
    description TEXT NOT NULL,
    beneficiary_name TEXT,
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    fund_source_code TEXT NOT NULL REFERENCES fund_sources(source_code),
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'submitted', 'approved', 'paid', 'void')),
    justification TEXT,
    evidence_path TEXT,
    created_by_user_id UUID REFERENCES users(id),
    approved_by_user_id UUID REFERENCES users(id),
    paid_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS disbursement_events (
    id BIGSERIAL PRIMARY KEY,
    disbursement_id UUID NOT NULL REFERENCES disbursements(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('created', 'updated', 'submitted', 'approved', 'paid', 'voided')),
    actor_user_id UUID REFERENCES users(id),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_disbursements_date_status ON disbursements(output_date, status);
CREATE INDEX IF NOT EXISTS idx_disbursements_fund_source ON disbursements(fund_source_code);
CREATE INDEX IF NOT EXISTS idx_disbursements_category_date ON disbursements(category, output_date);
CREATE INDEX IF NOT EXISTS idx_disbursement_events_disbursement_time ON disbursement_events(disbursement_id, created_at);

COMMIT;
