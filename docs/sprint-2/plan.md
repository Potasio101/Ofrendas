# Sprint 2 Plan - Auth/RBAC Hardening and Timezone Normalization

Sprint window: 1 week
Branch: feature/sprint-2
Owner: Dev team (Nova/Sage/Milo)
QA owner: Ivy
Producer: Remy

## Sprint Goal

Harden access and data consistency for production-shaped operations:
- Enforce role-based access for treasurer/admin/auditor
- Normalize timezone handling for day-based workflows
- Prepare first expansion hooks for cash window and outputs modules

## In Scope

1. Authentication and role context baseline
- Introduce request-level user identity context
- Define role assignment source for local/dev mode
- Add route guard helpers for role checks

2. RBAC enforcement in existing routes
- Treasurer permissions for capture/review/confirm/edit operations
- Admin permissions for config and privileged operations (initial placeholders)
- Auditor read-only behavior for day-log/summary/audit views

3. Timezone normalization
- Define canonical timezone policy (storage UTC, display local TZ)
- Ensure day-log and summary queries use deterministic timezone conversion
- Remove host/container date ambiguity in tests and QA checks

4. Module expansion preparation
- Add minimal service/repository interfaces for cash window and outputs entry points
- Keep full workflows out of scope for this sprint

5. Test and QA baseline
- Add tests for RBAC denies/allows on critical routes
- Add tests for date-boundary behavior under configured timezone
- Update QA checklist for role behavior and timezone-sensitive validations

## Out of Scope

- Full user management UI
- External identity provider integration
- Complete cash window workflow implementation
- Complete outputs approval workflow implementation

## Acceptance Criteria

Functional:
- Unauthorized role cannot execute protected write actions.
- Auditor can access read-only views and is blocked from write actions.
- Day-log results are deterministic for the configured timezone across environments.
- Existing Sprint 1 flow still works for treasurer role.

Non-functional:
- No hardcoded credentials or role bypass in production configuration paths.
- Route-level authorization failures are logged consistently.
- Test suite includes regression coverage for protected routes.

Quality gates:
- Unit/integration tests pass in Docker.
- QA playthrough completed with role matrix and timezone cases.

## Work Breakdown

1. Backend hardening (Sage)
- Implement auth context, RBAC guards, and timezone query handling.
- Add integration tests for protected endpoints.

2. Frontend UX adjustments (Nova + Milo)
- Hide/disable actions that are not allowed for current role.
- Clarify denial messages and keep mobile-first readability.

3. QA execution (Ivy)
- Validate role matrix and timezone boundary cases.
- File issues for regressions and authorization gaps.

4. Producer coordination (Remy)
- Track scope and merge readiness.
- Ensure docs/progress updates are continuous.

## Definition of Done

- Sprint 2 scope merged to main.
- docs/sprint-2/progress.md reflects final checklist and issue links.
- docs/sprint-2/done.md includes validation evidence and unresolved risks.
- QA sign-off note created (or blocked with explicit issue ids).
