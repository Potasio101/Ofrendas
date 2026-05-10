# Sprint 8 Done Handoff

Status: Completed (Ready for PR)
Branch: feature/sprint-8

## What Was Delivered

- Async training orchestration service with background execution and single-job lock (`TrainingJobService`).
- Request-safe fallback implementation for environments without training backend (`NoopTrainingJobService`).
- Training job/artifact persistence model in PostgreSQL repository and migration `0008_training_jobs_and_model_artifacts.sql`.
- Admin-only training operational endpoints:
	- `POST /admin/training/force`
	- `GET /admin/training/status`
	- `GET /admin/training/jobs`
- App wiring update in `main.py` to inject training service into Flask app factory.
- New regression tests for async job lifecycle and endpoint RBAC.

## Validation Summary

- Tests run: `docker compose build app`
- Tests run: `docker compose run --rm app pytest -q tests/test_training_job_service.py tests/test_app_training_endpoints.py`
- Tests run: `docker compose run --rm app pytest -q .`
- Result: Green (`6 passed` focused Sprint 8 tests, `66 passed` full suite).
- QA sign-off: Approved (`docs/qa/sprint-8-signoff.md`).

## Issues Found and Resolved

- Issue: Newly added tests were not visible in Docker test run.
- Resolution: Rebuilt app image with `docker compose build app` and reran tests successfully.

## Remaining Risks

- Thread-based runner is appropriate for current scope but should be reviewed when workload or multi-worker scale grows.

## Next Sprint Inputs

- Sprint 9 can focus on model promotion controls, rollback safety, and operational admin UX hardening over the now-persisted training lifecycle.

## Handoff Commands

- `docker compose run --rm app python -m pytest -q`
