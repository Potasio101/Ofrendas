# Sprint 10 Done Handoff

Status: Completed on feature branch, pending merge

## What Was Delivered

- Runtime OCR debug service with admin-controlled ON/OFF behavior.
- OCR debug artifact capture under `/app/data/ocr-debug/<request_id>/` including:
  - `input.jpg`
  - `preprocessed.jpg`
  - `name_roi.jpg`
  - `diezmo_roi.jpg`
  - `ofrenda_roi.jpg`
  - `ocr_raw.json`
  - `parsed_fields.json`
  - `timings.json`
  - `meta.json`
- Admin endpoints for OCR debug status, toggle, sessions list, and session detail.
- New `/admin` dashboard page with OCR debug status panel, toggle action, and latest sessions view.
- Retention and max-session trimming logic for debug artifacts.
- Structured debug write failure logging with event `ocr_debug_write_failed` and request context.
- Test coverage for RBAC, toggle flow, artifacts ON/OFF behavior, and write-failure tolerance.

## Validation Summary

- Docker image rebuilt successfully.
- Focused endpoint test command executed:
  - `docker compose run --rm app pytest -q tests/test_app_training_endpoints.py`
  - Result: skipped (file not present on this branch baseline).
- Full Docker suite command executed:
  - `docker compose run --rm app pytest -q .`
  - Result: passed with Sprint 10 tests included.

## Issues Found and Resolved

- Branch baseline did not include prior Sprint 9 files (`/admin` dashboard and `tests/test_app_training_endpoints.py`), so Sprint 10 included the required admin dashboard and OCR debug controls directly in this branch.

## Remaining Risks

- Debug artifacts currently use local filesystem storage; horizontal scaling needs shared artifact storage in future.
- ROI crop coordinates remain static; envelope template drift can still reduce extraction quality.

## Next Sprint Inputs

- Add guided ROI calibration workflow in admin for envelope template tuning.
- Add downloadable debug bundle export for faster QA/ops handoff.
- Add per-field OCR confidence heatmap in session detail view.
