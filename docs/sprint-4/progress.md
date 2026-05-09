# Sprint 4 Progress Tracker

Status: Ready for merge
Last update: 2026-05-08

## Checklist

- [x] Branch created: feature/sprint-4
- [x] Sprint 4 planning docs created
- [x] Cash line upsert/recalculate implemented
- [x] Cash close/reopen transitions implemented
- [x] Outputs submit/approve/paid transitions implemented
- [x] Transition audit events verified
- [x] Tests for Sprint 4 scope passing
- [x] QA playthrough completed
- [ ] Merge to main completed

## Phase Notes

Phase 0 - Planning
- Sprint 4 started from Sprint 3 completed state on main.
- Scope focus set to full cash window workflow and outputs approvals.
- Branch `feature/sprint-4` created.

Phase 1 - Build
- Implemented cash session line upsert with recalculation and event writes (`line_update`, `recalculate`).
- Implemented cash session close and reopen transitions with transition guards and event writes (`close`, `reopen`).
- Implemented outputs draft update and workflow transitions (`submit`, `approve`, `pay`) with status guards and event writes.
- Added new workflow routes and RBAC policy entries for cash and outputs transitions.

Phase 2 - Test and QA
- Extended module route tests for transition endpoints and deny paths in `tests/test_app_modules.py`.
- Docker test run after Sprint 4 workflow implementation: 33 passed.
- Runtime smoke validation completed for cash and outputs transitions (open/line/close/reopen + draft/submit/approve/pay).
- QA sign-off published at `docs/qa/sprint-4-signoff.md`.

Phase 3 - Merge and Handoff
- Sprint 4 scope is merge-ready.
- Pending only: merge branch to main and finalize sprint done handoff.

## Open Blockers

- None.

## Related Issues

- None yet.
