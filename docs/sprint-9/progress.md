# Sprint 9 Progress

Status: Completed (Dev + QA)
Branch: feature/sprint-9
Goal: Model promotion, rollback, and ongoing operations.

## Daily Tracker

- Day 1:
  - Planned: Add model registry states and promotion/rollback data model.
  - Done: Added migration `0009_training_model_promotion_and_actions.sql`; extended artifact persistence with `candidate/active/archived/failed` states, promotion timestamps, and model-action audit events.
  - Risks: None.
- Day 2:
  - Planned: Implement promotion/rollback control plane and gate checks.
  - Done: Extended `TrainingJobService` with promotion gates, promote/rollback operations, active/candidate model status reporting, and action-log listing.
  - Risks: None.
- Day 3:
  - Planned: Add scheduled retraining safeguards.
  - Done: Added scheduled trigger path with minimum sample threshold, cooldown guard, and APScheduler nightly wiring in `main.py` with env-configurable schedule.
  - Risks: None.
- Day 4:
  - Planned: Add endpoint/UI integration and regression tests.
  - Done: Added admin APIs `POST /admin/training/promote`, `POST /admin/training/rollback`, `GET /admin/training/actions`; expanded `admin/config` response for model/action visibility; added/updated endpoint and service tests.
  - Risks: None.
- Day 5:
  - Planned: Close QA and finalize sprint artifacts.
  - Done: Docker build and focused/full pytest runs green; QA sign-off updated in `docs/qa/sprint-9-signoff.md`.
  - Risks: None.

## Scope Checklist

- [x] Model registry states implemented.
- [x] Promote/rollback APIs implemented with RBAC.
- [x] Promotion gates enforced.
- [x] Nightly scheduler with thresholds and cooldown.
- [x] Regression and control-plane tests passing.

## Evidence

- PR(s):
- Test command(s): `docker compose build app`
- Test command(s): `docker compose run --rm app pytest -q tests/test_training_job_service.py tests/test_app_training_endpoints.py`
- Test command(s): `docker compose run --rm app pytest -q .`
- Test result summary: Green (`12 passed` focused Sprint 9 tests, `72 passed` full suite).
- QA notes: QA sign-off approved in `docs/qa/sprint-9-signoff.md`.

## Open Risks

- No blocking risks identified within Sprint 9 scope.
