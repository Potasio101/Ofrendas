# Sprint 3 Progress Tracker

Status: Ready for merge
Last update: 2026-05-08

## Checklist

- [x] Branch created: feature/sprint-3
- [x] Sprint 3 planning docs created
- [x] Auth source abstraction implemented
- [x] Auth mode gating enforced (non-local hardening)
- [x] RBAC integration verified with auth source
- [x] Cash window skeleton routes/services added
- [x] Outputs skeleton routes/services added
- [x] Tests for Sprint 3 scope passing
- [x] QA playthrough completed
- [ ] Merge to main completed

## Phase Notes

Phase 0 - Planning
- Sprint 3 started from Sprint 2 completed state on main.
- Scope focus set to auth source hardening and module expansion kickoff.
- Branch `feature/sprint-3` created.

Phase 1 - Build
- Added `APP_AUTH_MODE` configuration with `local-dev` and `header-strict` modes.
- Implemented strict identity validation path (required role and user headers).
- Added structured authentication denial logs (`authn_denied`) for strict mode failures.
- Integrated strict auth checks with existing RBAC policy guard flow.
- Added cash window service skeleton and route stubs: `POST /cash-window/open`, `GET /cash-window`.
- Added outputs service skeleton and route stubs: `POST /outputs/draft`, `GET /outputs/drafts`.
- Added PostgreSQL repository skeleton operations for cash session open/read and disbursement draft create/list.

Phase 2 - Test and QA
- Added auth mode tests in `tests/test_app_auth_mode.py` for missing identity, invalid role, and valid strict-mode access.
- Added module skeleton route tests in `tests/test_app_modules.py`.
- Docker test run after Sprint 3 increments: 23 passed.
- Runtime smoke matrix validated cash window and outputs RBAC behavior.
- QA sign-off published at `docs/qa/sprint-3-signoff.md`.

Phase 3 - Merge and Handoff
- Sprint 3 scope is merge-ready.
- Pending only: merge branch to main and finalize sprint done handoff.

## Open Blockers

- None.

## Related Issues

- None yet.
