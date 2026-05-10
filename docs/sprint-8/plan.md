# Sprint 8 Plan - Async Training Pipeline and Job Control

Sprint window: 1 week
Branch: feature/sprint-8
Owner: Dev team (Nova/Sage/Milo)
QA owner: Ivy
Producer: Remy

## Sprint Goal

Ship the first async training pipeline with job state tracking and safe background execution.

## In Scope

1. Training job orchestration
- Add async training runner (separate from request path).
- Add job lock to avoid concurrent training runs.
- Define job lifecycle states: `queued`, `running`, `succeeded`, `failed`, `canceled`.

2. Dataset builder and trainer v1
- Build dataset from corrected samples.
- Add split strategy (time-based or deterministic split).
- Train correction model artifact v1 with metadata output.

3. Training persistence and status API
- Add training jobs table and model artifact metadata table.
- Add API endpoints:
  - `POST /admin/training/force`
  - `GET /admin/training/status`
  - `GET /admin/training/jobs`
- Restrict all endpoints to admin role.

4. Error handling and reliability
- Add retries for transient data read failures.
- Add clear failure reason and stack trace references in job logs.
- Ensure request-time OCR path stays responsive during training.

## Out of Scope

- Automatic model promotion to active strategy.
- A/B rollout by traffic percentage.
- UI dashboard polish beyond basic admin controls.

## Related ADRs

- ADR-012: Ongoing Training with Admin Force Trigger and Safe Promotion.

## Work Breakdown

1. Backend (Sage)
- Implement job runner, DB schema, and status APIs.
- Implement dataset builder and trainer v1.
- Add job lock and safe cancellation semantics.

2. Frontend/UI (Nova + Milo)
- Add basic admin page section for training controls and status list.
- Add force training action with confirmation guard.

3. QA (Ivy)
- Validate RBAC for all training endpoints.
- Validate concurrent force attempts only start one job.
- Validate failure states and recovery path.

4. Producer (Remy)
- Track architecture decisions and update sprint artifacts.
- Keep scope aligned to pipeline stability first.

## Acceptance Criteria

Functional:
- Admin can enqueue force training job.
- Job runs asynchronously and stores status/result metadata.
- Only one training job runs at a time.

Non-functional:
- Capture and review flows remain responsive under active training.
- Structured logs and status endpoints provide operational visibility.

Quality gates:
- Test suite passes in Docker.
- QA sign-off document published.

## Definition of Done

- Sprint 8 scope merged to main.
- `docs/sprint-8/progress.md` reflects final evidence.
- `docs/sprint-8/done.md` completed with risks and next inputs.
- `docs/qa/sprint-8-signoff.md` published (or blocked with issue ids).
