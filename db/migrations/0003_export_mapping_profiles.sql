-- 0003_export_mapping_profiles.sql
-- Adds schema-driven export mapping profiles and uploaded template tracking.

BEGIN;

CREATE TABLE IF NOT EXISTS export_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    provider TEXT NOT NULL CHECK (provider IN ('quickbooks_online', 'quickbooks_desktop', 'xero', 'zoho_books', 'sage', 'generic_csv')),
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT,
    created_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, version)
);

CREATE TABLE IF NOT EXISTS export_profile_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_profile_id UUID NOT NULL REFERENCES export_profiles(id) ON DELETE CASCADE,
    source_field TEXT NOT NULL,
    target_column TEXT NOT NULL,
    transform_type TEXT NOT NULL DEFAULT 'direct' CHECK (transform_type IN ('direct', 'default_value', 'concat', 'date_format', 'currency_format', 'custom_expression')),
    transform_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    default_value TEXT,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    output_order INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (export_profile_id, target_column),
    UNIQUE (export_profile_id, output_order)
);

CREATE TABLE IF NOT EXISTS export_template_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_profile_id UUID NOT NULL REFERENCES export_profiles(id) ON DELETE CASCADE,
    uploaded_by_user_id UUID REFERENCES users(id),
    original_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    detected_headers JSONB NOT NULL,
    parse_status TEXT NOT NULL DEFAULT 'parsed' CHECK (parse_status IN ('parsed', 'warning', 'failed')),
    parse_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_export_profiles_provider_active ON export_profiles(provider, is_active);
CREATE INDEX IF NOT EXISTS idx_export_profile_mappings_profile_order ON export_profile_mappings(export_profile_id, output_order);
CREATE INDEX IF NOT EXISTS idx_export_template_uploads_profile_created_at ON export_template_uploads(export_profile_id, created_at);

COMMIT;
