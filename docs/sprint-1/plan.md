# Sprint 1 Plan - Foundation and First Vertical Slice

Sprint window: 1 week
Branch: feature/sprint-1
Owner: Dev team (Nova/Sage/Milo)
QA owner: Ivy
Producer: Remy

## Sprint Goal

Deliver the first production-shaped vertical slice:
- Capture envelope image
- Review/correct fields
- Confirm record in PostgreSQL
- Show daily summary
- Support thin deferred correction with field-level audit

## In Scope

1. Application scaffold and dependency wiring
- Python project layout from Ofrenda.md
- Interface contracts for OCR, correction, storage, training
- Strategy implementation stubs with EasyOCR + fuzzy correction

2. Database and repositories
- Connect to PostgreSQL using env configuration
- Implement repository methods for core offering flows
- Wire review queue + field history writes

3. Core routes and UI
- GET /
- POST /process
- GET /review
- POST /confirm
- GET /summary
- GET /day-log
- GET /review/<offering_id>
- POST /review/<offering_id>/save

4. Security/ops baseline
- APP_ENV-driven config
- /healthz and /readyz
- Structured logging baseline

5. Test baseline
- Unit tests for service orchestration
- Integration test for confirm flow
- Integration test for deferred correction audit write

## Out of Scope

- Full kiosk POS workflow
- Full outputs/disbursements module
- Accounting export UI and mapping profile manager
- Cloudflare remote rollout

## Acceptance Criteria

Functional:
- User can upload an envelope image and reach review screen.
- User can correct at least name and amount fields and confirm record.
- Confirm persists data to PostgreSQL and appears in daily summary.
- User can reopen same-day record and save deferred correction.
- Deferred correction writes immutable field history (old/new, actor, timestamp, reason).

Non-functional:
- App starts from documented local run steps.
- No hardcoded secrets in repository.
- Health/readiness endpoints return success when dependencies are available.

Quality gates:
- Core tests pass in CI/local.
- QA executes playthrough and files issues for defects.

## Work Breakdown

1. Backend foundation (Sage)
- Build interfaces/models/services skeleton.
- Implement repository contracts for core entities.

2. Frontend foundation (Nova + Milo)
- Mobile-first templates for home, review, day-log, summary.
- Ensure touch-friendly layout and clear action hierarchy.

3. QA baseline (Ivy)
- Prepare test checklist.
- Validate role behavior and audit field correctness.

4. Producer coordination (Remy)
- Track issues, scope changes, and merge readiness.

## Definition of Done

- Code merged to main with sprint scope complete.
- docs/sprint-1/progress.md updated with final status and issue references.
- docs/sprint-1/done.md completed with handoff notes.
- QA sign-off note created (or explicit blocked status with issue ids).
