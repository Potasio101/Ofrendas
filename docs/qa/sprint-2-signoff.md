# QA Sign-off - Sprint 2

Date: 2026-05-08
QA Owner: Ivy
Status: PASS (auth/rbac + timezone scope)

## Scope Validated

- RBAC policy enforcement on read/write routes.
- Admin-only guard behavior on `/admin/config`.
- Confirm path role restrictions and successful treasurer flow.
- Day-log read access for auditor role.
- Health/readiness checks on running Docker stack.
- Regression suite including RBAC and timezone coverage.

## Evidence Summary

1. Automated tests in Docker: 14 passed.
2. `GET /healthz` returned HTTP 200.
3. `GET /readyz` returned HTTP 200.
4. `GET /admin/config` returned:
   - admin: 200
   - treasurer: 403
   - auditor: 403
5. `POST /confirm` returned:
   - auditor: 403
   - treasurer: 302
6. `GET /day-log` returned:
   - auditor: 200
7. QA data date aligned using app runtime date (`docker exec -i ofrendas-app date +%F`).

## Notes

- Service date now resolves from PostgreSQL clock with configured timezone and Python fallback.
- Invalid actor identifier input is normalized in service layer to prevent UUID-related persistence failures.

## Open Issues

- None filed for Sprint 2 scope.

## Recommendation

Approve Sprint 2 for merge readiness.
