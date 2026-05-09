# PostgreSQL migrations

This folder contains versioned SQL migrations for the offerings app.

## Files

- 0001_init_core.sql
- 0002_audit_and_exports.sql
- 0003_export_mapping_profiles.sql
- 0004_review_queue_and_field_history.sql
- 0005_cash_window_and_counting.sql
- 0006_kiosk_pos_mode.sql
- 0007_outputs_and_disbursements.sql

Apply in numeric order.

## Run with psql

Example:

```bash
export DATABASE_URL="postgresql://ofrendas:ofrendas@localhost:5432/ofrendas"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/0001_init_core.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/0002_audit_and_exports.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/0003_export_mapping_profiles.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/0004_review_queue_and_field_history.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/0005_cash_window_and_counting.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/0006_kiosk_pos_mode.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/0007_outputs_and_disbursements.sql
```

## Run against Docker postgres

If your DB container is named postgres:

```bash
docker exec -i postgres psql -U ofrendas -d ofrendas -v ON_ERROR_STOP=1 < db/migrations/0001_init_core.sql
docker exec -i postgres psql -U ofrendas -d ofrendas -v ON_ERROR_STOP=1 < db/migrations/0002_audit_and_exports.sql
docker exec -i postgres psql -U ofrendas -d ofrendas -v ON_ERROR_STOP=1 < db/migrations/0003_export_mapping_profiles.sql
docker exec -i postgres psql -U ofrendas -d ofrendas -v ON_ERROR_STOP=1 < db/migrations/0004_review_queue_and_field_history.sql
docker exec -i postgres psql -U ofrendas -d ofrendas -v ON_ERROR_STOP=1 < db/migrations/0005_cash_window_and_counting.sql
docker exec -i postgres psql -U ofrendas -d ofrendas -v ON_ERROR_STOP=1 < db/migrations/0006_kiosk_pos_mode.sql
docker exec -i postgres psql -U ofrendas -d ofrendas -v ON_ERROR_STOP=1 < db/migrations/0007_outputs_and_disbursements.sql
```

## Notes

- Migrations are additive and idempotent where practical.
- Keep changes forward-only and add a new numbered file per change.
- Record schema decisions in ADR files under docs/architecture.
