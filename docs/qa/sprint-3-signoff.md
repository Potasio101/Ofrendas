# QA Sign-off - Sprint 3

Date: 2026-05-08
QA Owner: Ivy
Status: PASS (auth mode + module skeleton scope)

## Scope Validated

- Auth mode hardening (`local-dev` and `header-strict`) integrated with RBAC checks.
- Cash window skeleton endpoints with role constraints.
- Outputs draft skeleton endpoints with role constraints.
- Existing protected route behavior retained.
- Regression suite passing in Docker.

## Evidence Summary

1. Automated tests in Docker: 23 passed.
2. Runtime smoke matrix on app container:
   - `POST /cash-window/open`:
     - treasurer: 200
     - auditor: 403
   - `GET /cash-window?service_date=<app_today>`:
     - auditor: 200
   - `POST /outputs/draft`:
     - admin: 201
     - auditor: 403
   - `GET /outputs/drafts?output_date=<app_today>`:
     - auditor: 200
3. Smoke data cleanup verified in PostgreSQL (`description='S3 Smoke Draft'` count = 0).

## Notes

- Outputs draft endpoint expects form fields; JSON payload attempts return 400 by design in current implementation.
- Strict auth mode behavior is covered in automated tests for missing identity and invalid role headers.

## Open Issues

- None filed for Sprint 3 current scope.

## Recommendation

Approve Sprint 3 for merge readiness.
