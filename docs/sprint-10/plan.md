# Sprint 10 Plan - OCR Debug Runtime Observability and Admin Controls

Sprint window: 1 week  
Branch: feature/sprint-10  
Owner: Dev team (Nova/Sage/Milo)  
QA owner: Ivy  
Producer: Remy

## Sprint Goal

Enable admin-controlled OCR debug ON/OFF at runtime to troubleshoot extraction failures with auditable artifacts and retention controls.

## In Scope

1. OCR debug runtime configuration and defaults
- Add `OCR_DEBUG_ENABLED=false` (default).
- Add `OCR_DEBUG_RETENTION_DAYS=7`.
- Add `OCR_DEBUG_MAX_SESSIONS=500`.

2. Admin-only OCR debug control plane
- Add `GET /admin/ocr-debug/status`.
- Add `POST /admin/ocr-debug/toggle`.
- Add `GET /admin/ocr-debug/sessions?limit=20`.
- Add `GET /admin/ocr-debug/session/<request_id>`.

3. OCR debug artifacts and observability
- Persist artifacts under `/app/data/ocr-debug/<request_id>/`.
- Save `input.jpg`, `preprocessed.jpg`, `name_roi.jpg`, `diezmo_roi.jpg`, `ofrenda_roi.jpg`.
- Save `ocr_raw.json`, `parsed_fields.json`, `timings.json`, `meta.json`.

4. Reliability and safety
- Debug write failures must not break `/process`.
- Emit structured log event `ocr_debug_write_failed` with `request_id`.
- Restrict debug access to admin routes only.

5. Admin UI dashboard
- Add `/admin` page block for OCR debug status, toggle control, latest sessions, and session detail access.

6. Tests and Docker validation
- Add/extend tests for RBAC, toggle transitions, artifacts ON/OFF, and write-failure tolerance.
- Run Docker build + focused/full pytest required by sprint closure.

## Out of Scope

- OCR model retraining pipeline changes.
- New OCR engine swap or model architecture changes.
- Multi-node artifact storage distribution.

## Acceptance Criteria

Functional:
- `/admin` renders for admin without 500.
- OCR debug can be toggled ON/OFF at runtime without restart.
- Artifacts are created only when debug is ON.
- Non-admin users receive 403 on OCR debug endpoints.

Non-functional:
- Retention and max-session trimming are enforced.
- Debug write errors are logged and do not interrupt core capture flow.
- Docker tests pass for sprint scope and regressions.

## Definition of Done

- Sprint 10 docs completed (`plan`, `progress`, `done`, QA sign-off).
- ADR created for OCR debug runtime toggle decision.
- PROJECT_BRIEF sections 7 and 8 updated for sprint closure.
