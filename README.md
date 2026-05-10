# Ofrendas

Documentacion de arquitectura y plan de implementacion para la app de digitalizacion de sobres de ofrenda.

## Alcance actual

- Source of truth operativo: PostgreSQL.
- Visualizacion y reportes diarios: desde la app.
- SharePoint: fuera del alcance actual.
- Integracion de export a SharePoint: fase futura, no prioritaria.

## Documentos

- Arquitectura principal y runbook: `Ofrenda.md`
- Brief operativo de orquestacion: `PROJECT_BRIEF.md`
- Decisiones formales de arquitectura: `docs/architecture/`
- Migraciones PostgreSQL: `db/migrations/`

## Matriz de autenticacion por entorno

### APP_ENV=local

- `APP_AUTH_MODE=local-dev` (default): permitido para desarrollo local.
- `APP_AUTH_MODE=header-strict`: permitido para pruebas con headers de identidad.
- `APP_AUTH_MODE=proxy-token`: permitido si `APP_AUTH_PROXY_TOKEN` esta configurado.
- `APP_AUTH_MODE=proxy-signed`: permitido si `APP_AUTH_PROXY_SIGNING_SECRET` esta configurado.

### APP_ENV=production

- `APP_AUTH_MODE=local-dev`: no permitido. La app falla en startup.
- `APP_AUTH_MODE=header-strict`: permitido.
- `APP_AUTH_MODE=proxy-token`: permitido solo si `APP_AUTH_PROXY_TOKEN` existe.
- `APP_AUTH_MODE=proxy-signed`: permitido solo si `APP_AUTH_PROXY_SIGNING_SECRET` existe.

Variables relevantes:

- `APP_ENV`: `local` o `production`.
- `APP_AUTH_MODE`: `local-dev`, `header-strict`, `proxy-token`, `proxy-signed`.
- `APP_AUTH_PROXY_TOKEN`: requerido en production con `proxy-token`.
- `APP_AUTH_PROXY_SIGNING_SECRET`: requerido en production con `proxy-signed`.
- `APP_AUTH_PROXY_MAX_AGE_SECONDS`: ventana de frescura para `proxy-signed`.

## Inicio de construccion (orquestacion)

1. Leer `PROJECT_BRIEF.md` completo.
2. Ejecutar Sprint 1 usando:
	- `docs/sprint-1/plan.md`
	- `docs/sprint-1/progress.md`
	- `docs/sprint-1/done.md`
3. Revisar debate inicial y decisiones de alcance en:
	- `docs/brainstorm/brainstorm-001.md`

## Glosario operativo (onboarding rapido)

- Fuente autoritativa: sistema que manda para un dataset cuando hay conflicto.
- Source-of-truth matrix: tabla que define dataset, escritura, sync y politica de conflicto.
- Sync async: sincronizacion en background por jobs, sin bloquear captura en UI.
- Fallback queue: cola local durable para reintentos de destinos de export opcionales.
- Reconciliacion: proceso programado que drena pendientes y valida consistencia.
- Idempotencia: misma operacion repetida sin duplicar efectos (ej. export IDs unicos).

## ADRs

- `docs/architecture/ADR-001-runtime-and-deployment-topology.md`
- `docs/architecture/ADR-002-storage-resilience-sharepoint-fallback.md`
- `docs/architecture/ADR-003-environment-config-and-secrets.md`
- `docs/architecture/ADR-004-cloudflare-tunnel-low-cost-ingress.md`
- `docs/architecture/ADR-005-accounting-exports-multi-provider.md`
- `docs/architecture/ADR-006-postgresql-reporting-with-sharepoint-complement.md`
- `docs/architecture/ADR-007-schema-driven-csv-mapping.md`
- `docs/architecture/ADR-008-deferred-correction-and-field-audit.md`
- `docs/architecture/ADR-009-cash-window-and-daily-close-audit.md`
- `docs/architecture/ADR-010-kiosk-pos-cash-zelle-custom-items.md`
- `docs/architecture/ADR-011-outputs-fund-source-and-approval.md`
- `docs/architecture/ADR-012-ocr-debug-runtime-admin-toggle.md`

## OCR Debug runtime controls

- `OCR_DEBUG_ENABLED` (default `false`)
- `OCR_DEBUG_RETENTION_DAYS` (default `7`)
- `OCR_DEBUG_MAX_SESSIONS` (default `500`)
- `OCR_DEBUG_PATH` (default `/app/data/ocr-debug`)

## Base de datos

- Guia de ejecucion de migraciones: `db/migrations/README.md`
- Migracion inicial core: `db/migrations/0001_init_core.sql`
- Migracion auditoria/exportes: `db/migrations/0002_audit_and_exports.sql`
- Migracion perfiles de mapping: `db/migrations/0003_export_mapping_profiles.sql`
- Migracion cola de revision e historial por campo: `db/migrations/0004_review_queue_and_field_history.sql`
- Migracion ventana de cash y cierre diario: `db/migrations/0005_cash_window_and_counting.sql`
- Migracion kiosk POS (cash/zelle/custom items): `db/migrations/0006_kiosk_pos_mode.sql`
- Migracion salidas/desembolsos con fondo origen: `db/migrations/0007_outputs_and_disbursements.sql`

## PostgreSQL con Docker

Arranque rapido local:

```bash
docker compose up -d postgres
docker compose ps
```

Aplicar migraciones:

```bash
for f in db/migrations/000[1-7]*.sql; do
	docker exec -i ofrendas-postgres psql -U ofrendas -d ofrendas -v ON_ERROR_STOP=1 < "$f"
done
```

Connection string local de la app:

```env
DATABASE_URL=postgresql://ofrendas:ofrendas@localhost:5432/ofrendas
```

## App + PostgreSQL con Docker

Levantar stack completo:

```bash
docker compose up -d --build app
docker compose ps
```

Verificar endpoints de la app:

```bash
curl http://localhost:5001/healthz
curl http://localhost:5001/readyz
```

Ejecutar tests:

```bash
docker compose run --rm app python -m pytest -q
```

Si agregas nuevos tests y quieres asegurar imagen actualizada:

```bash
docker compose build app
docker compose run --rm app python -m pytest -q
```

QA Sprint 1 sign-off:

- `docs/qa/sprint-1-signoff.md`

Nota para pruebas de Day Log:

- Si validas por fecha, usa la fecha del contenedor de app para evitar desfase de timezone:

```bash
docker exec -i ofrendas-app date +%F
```

## UX / Figma Handoff

- JTBD: `docs/ux/ofrendas-core-jtbd.md`
- User Journey: `docs/ux/ofrendas-core-journey.md`
- Flow + Accessibility: `docs/ux/ofrendas-core-flow.md`
