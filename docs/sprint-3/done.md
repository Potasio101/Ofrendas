# Sprint 3 Done Handoff

Status: Ready for merge

## What Was Delivered

- Auth source hardening increment with configurable auth mode (`local-dev`, `header-strict`).
- Strict identity checks integrated into existing RBAC policy guard flow.
- Authentication denial audit logging (`authn_denied`) for strict mode failures.
- Cash window module skeleton: service + repository + routes (`POST /cash-window/open`, `GET /cash-window`).
- Outputs module skeleton: service + repository + routes (`POST /outputs/draft`, `GET /outputs/drafts`).
- Expanded automated tests for auth mode and module skeleton endpoints.
- QA sign-off artifact for Sprint 3 scope.

## Validation Summary

- Docker test suite result after Sprint 3 increments: 23 passed.
- Runtime smoke checks on app container:
	- `POST /cash-window/open`: treasurer 200, auditor 403
	- `GET /cash-window?service_date=<app_today>`: auditor 200
	- `POST /outputs/draft`: admin 201, auditor 403
	- `GET /outputs/drafts?output_date=<app_today>`: auditor 200
- Smoke data cleanup in PostgreSQL verified (`S3 Smoke Draft` records = 0).
- QA sign-off published at `docs/qa/sprint-3-signoff.md`.

## Issues Found and Resolved

- Smoke cleanup initially failed due to wrong DB user (`postgres` role unavailable).
- Resolution: use configured DB user (`ofrendas`) for cleanup commands.

## Remaining Risks

- Auth mode currently trusts headers in strict mode without external identity provider verification.
- Module routes are skeleton-level and require full business workflows in future sprints.
- Outputs draft endpoint currently expects form-data only.

## Next Sprint Inputs

- Integrate stronger non-local auth source (proxy or identity provider validation).
- Expand cash window flow with denomination lines and close/reopen controls.
- Expand outputs flow with approval transitions and event audit enrichment.
- Add integration tests for repository operations against PostgreSQL container.

## Handoff Commands

Read PROJECT_BRIEF.md and docs/sprint-3/progress.md.
Continue from unresolved tasks and open issues.
