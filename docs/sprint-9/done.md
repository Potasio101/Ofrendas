# Sprint 9 Done Handoff

Status: Completed (Ready for PR)
Branch: feature/sprint-9

## What Was Delivered

- Model registry and promotion lifecycle support for artifacts (`candidate`, `active`, `archived`, `failed`) with migration `0009_training_model_promotion_and_actions.sql`.
- Backend control-plane methods for promote/rollback plus model action logging in PostgreSQL repository.
- Training service upgrades for promotion gate evaluation (`name_match_precision`, `amount_parse_accuracy`, `fallback_reduction`) and model control operations.
- Scheduled nightly retraining trigger with minimum sample threshold and cooldown safeguards wired via APScheduler in `main.py`.
- Admin-only operational APIs:
  - `POST /admin/training/promote`
  - `POST /admin/training/rollback`
  - `GET /admin/training/actions`
- Admin config payload now exposes active/candidate model state and recent training action logs.
- Expanded test coverage for sprint-9 control plane in `tests/test_training_job_service.py` and `tests/test_app_training_endpoints.py`.

## Validation Summary

- Tests run: `docker compose build app`
- Tests run: `docker compose run --rm app pytest -q tests/test_training_job_service.py tests/test_app_training_endpoints.py`
- Tests run: `docker compose run --rm app pytest -q .`
- Result: Green (`12 passed` focused Sprint 9 tests, `72 passed` full suite).
- QA sign-off: Approved (`docs/qa/sprint-9-signoff.md`).

## Issues Found and Resolved

- Issue: Local host Python environment is Python 3.9 and missing project runtime dependencies for direct local pytest.
- Resolution: Executed sprint validation through Docker app image using project-standard compose commands.

## Remaining Risks

- Scheduler should run in a single-worker/process context in production to avoid duplicate scheduled triggers; keep `TRAINING_SCHEDULER_ENABLED` scoped to one runtime.

## Next Sprint Inputs

- Sprint 10 should focus on operator dashboards and runbook refinement around promotion outcomes, plus richer model quality metrics.

## Handoff Commands

- `docker compose run --rm app python -m pytest -q`
