# Sprint 2 Progress Tracker

Status: In progress
Last update: 2026-05-08

## Checklist

- [x] Branch created: feature/sprint-2
- [x] Sprint 2 planning docs created
- [x] Auth context baseline implemented
- [x] RBAC guard helpers implemented
- [x] RBAC enforced on critical routes
- [x] Timezone policy documented and implemented
- [x] Route-level RBAC regression tests added
- [ ] QA playthrough completed
- [ ] Merge to main completed

## Phase Notes

Phase 0 - Planning
- Sprint 2 scope approved from Sprint 1 handoff risks.
- Focus set to auth/RBAC hardening + timezone normalization.
- Branch `feature/sprint-2` created.

Phase 1 - Build
- Request auth context implemented using `X-User-Role` and `X-User-Id` headers with local defaults.
- RBAC route guard added and enforced on critical write paths: `/process`, `/confirm`, `/review/<offering_id>/save`.
- Read paths (`/`, `/summary`, `/day-log`, `/review/<offering_id>`) constrained to known roles.
- Day-based route queries now use timezone-aware current date derived from `APP_TIMEZONE`.
- Current service date now resolves from PostgreSQL clock with configured timezone, with Python fallback only if storage resolver fails.

Phase 2 - Test and QA
- Added route-level RBAC tests in `tests/test_app_rbac.py`.
- Docker test run after rebuild: 8 passed.
- Added timezone route tests in `tests/test_app_timezone.py` to validate DB-backed date resolution path.

Phase 3 - Merge and Handoff
- Pending.

## Open Blockers

- None.

## Related Issues

- None yet.
