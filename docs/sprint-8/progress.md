# Sprint 8 Progress

Status: Completed (Dev + QA)
Branch: feature/sprint-8
Goal: Async training pipeline and job control.

## Daily Tracker

- Day 1:
  - Planned: Implement async training runner with lifecycle persistence and admin-safe trigger.
  - Done: Added `TrainingJobService` with single-job lock, lifecycle states (`queued`, `running`, `succeeded`, `failed`), dataset build/split/training flow, and no-op fallback service for test-safe app boot.
  - Risks: None.
- Day 2:
  - Planned: Persist training jobs/artifacts and expose operational APIs.
  - Done: Added migration `0008_training_jobs_and_model_artifacts.sql`; implemented repository methods for job/artifact create/update/list/get; added admin endpoints `POST /admin/training/force`, `GET /admin/training/status`, `GET /admin/training/jobs`.
  - Risks: None.
- Day 3:
  - Planned: Validate RBAC and async behavior with targeted tests.
  - Done: Added `tests/test_training_job_service.py` and `tests/test_app_training_endpoints.py` covering job execution lifecycle and admin-only endpoint access.
  - Risks: Resolved by rebuilding Docker image so new test files are included.
- Day 4:
  - Planned: Run full docker regression and close QA evidence.
  - Done: Executed focused and full test suites in Docker with green results.
  - Risks: None.
- Day 5:
  - Planned:
  - Done:
  - Risks:

## Scope Checklist

- [x] Training job runner implemented.
- [x] Job state lifecycle persisted.
- [x] Force-training API endpoints added with RBAC.
- [x] Concurrent training lock implemented.
- [x] Regression and job-path tests passing.

## Evidence

- PR(s):
- Test command(s): `docker compose build app`
- Test command(s): `docker compose run --rm app pytest -q tests/test_training_job_service.py tests/test_app_training_endpoints.py`
- Test command(s): `docker compose run --rm app pytest -q .`
- Test result summary: Green (`6 passed` focused Sprint 8 tests, `66 passed` full suite).
- QA notes: QA sign-off approved in `docs/qa/sprint-8-signoff.md`.

## Open Risks

- No blocking risks identified within Sprint 8 scope.
