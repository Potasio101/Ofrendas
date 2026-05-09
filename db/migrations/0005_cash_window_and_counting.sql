-- 0005_cash_window_and_counting.sql
-- Adds daily cash window with denomination counting and audited close.

BEGIN;

CREATE TABLE IF NOT EXISTS cash_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_date DATE NOT NULL,
    session_status TEXT NOT NULL DEFAULT 'open' CHECK (session_status IN ('open', 'closed')),
    expected_cash_total NUMERIC(12,2) NOT NULL DEFAULT 0,
    counted_cash_total NUMERIC(12,2) NOT NULL DEFAULT 0,
    variance_total NUMERIC(12,2) NOT NULL DEFAULT 0,
    notes TEXT,
    opened_by_user_id UUID REFERENCES users(id),
    closed_by_user_id UUID REFERENCES users(id),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    UNIQUE (service_date)
);

CREATE TABLE IF NOT EXISTS cash_count_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cash_session_id UUID NOT NULL REFERENCES cash_sessions(id) ON DELETE CASCADE,
    denomination_value NUMERIC(12,2) NOT NULL,
    denomination_type TEXT NOT NULL CHECK (denomination_type IN ('bill', 'coin')),
    quantity INTEGER NOT NULL DEFAULT 0,
    line_total NUMERIC(12,2) NOT NULL DEFAULT 0,
    updated_by_user_id UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (cash_session_id, denomination_value, denomination_type)
);

CREATE TABLE IF NOT EXISTS cash_session_events (
    id BIGSERIAL PRIMARY KEY,
    cash_session_id UUID NOT NULL REFERENCES cash_sessions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('open', 'line_update', 'recalculate', 'close', 'reopen')),
    actor_user_id UUID REFERENCES users(id),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cash_sessions_service_date_status ON cash_sessions(service_date, session_status);
CREATE INDEX IF NOT EXISTS idx_cash_count_lines_session ON cash_count_lines(cash_session_id);
CREATE INDEX IF NOT EXISTS idx_cash_session_events_session_time ON cash_session_events(cash_session_id, created_at);

COMMIT;
