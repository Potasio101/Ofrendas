-- 0001_init_core.sql
-- Core schema for offerings app reporting and operations.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('treasurer', 'admin', 'auditor')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS offerings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_date DATE NOT NULL,
    service_day TEXT NOT NULL CHECK (service_day IN ('tuesday', 'thursday', 'sunday')),
    member_name TEXT NOT NULL,
    payment_method TEXT,
    diezmo NUMERIC(12,2) NOT NULL DEFAULT 0,
    ofrenda NUMERIC(12,2) NOT NULL DEFAULT 0,
    primicias NUMERIC(12,2) NOT NULL DEFAULT 0,
    pro_templo NUMERIC(12,2) NOT NULL DEFAULT 0,
    ofrenda_misionera NUMERIC(12,2) NOT NULL DEFAULT 0,
    ofrenda_pastoral NUMERIC(12,2) NOT NULL DEFAULT 0,
    total NUMERIC(12,2) NOT NULL DEFAULT 0,
    image_path TEXT,
    ocr_confidence NUMERIC(5,4),
    status TEXT NOT NULL DEFAULT 'confirmed' CHECK (status IN ('captured', 'confirmed', 'exported', 'reconciled')),
    source_channel TEXT NOT NULL DEFAULT 'mobile',
    captured_by_user_id UUID REFERENCES users(id),
    confirmed_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS offering_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    offering_id UUID NOT NULL REFERENCES offerings(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    ocr_value TEXT,
    corrected_value TEXT NOT NULL,
    confidence NUMERIC(5,4),
    corrected_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sync_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL CHECK (event_type IN ('sharepoint_write', 'sharepoint_reconcile', 'export_delivery')),
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'success', 'failed')),
    retries INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_offerings_service_date ON offerings(service_date);
CREATE INDEX IF NOT EXISTS idx_offerings_member_name ON offerings(member_name);
CREATE INDEX IF NOT EXISTS idx_offerings_status ON offerings(status);
CREATE INDEX IF NOT EXISTS idx_offering_corrections_offering_id ON offering_corrections(offering_id);
CREATE INDEX IF NOT EXISTS idx_sync_events_status_created_at ON sync_events(status, created_at);

COMMIT;
