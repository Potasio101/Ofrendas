# Sprint 5 Plan - Identity Provider Integration and Workflow UX Hardening

Sprint window: 1 week
Branch: feature/sprint-5
Owner: Dev team (Nova/Sage/Milo)
QA owner: Ivy
Producer: Remy

## Sprint Goal

Harden non-local authentication by introducing a trusted proxy identity mode and improve operator workflow UX for cash and outputs transitions.

## In Scope

1. Identity provider/proxy integration baseline
- Add `proxy-token` auth mode for non-local deployments.
- Require trusted proxy token plus identity headers.
- Reject missing/invalid proxy token requests with explicit authn denial logs.

2. Auth mode safety improvements
- Keep `local-dev` and `header-strict` modes for local/test workflows.
- Ensure role validation applies consistently across all auth modes.
- Add deterministic auth mode tests for proxy-token mode.

3. Workflow UX hardening
- Add transition summary info in JSON responses (from/to status and actor context where safe).
- Improve validation messages for transition endpoints.
- Keep RBAC restrictions unchanged and test deny paths.

4. Test and QA baseline
- Add tests for proxy-token auth mode and invalid token paths.
- Run runtime smoke checks for auth + transition endpoints.
- Publish QA sign-off artifact for sprint scope.

## Out of Scope

- Full external OAuth/OIDC login UI.
- MFA and session management screens.
- Notification delivery channels for workflow transitions.

## Acceptance Criteria

Functional:
- `proxy-token` mode rejects requests without valid proxy token.
- Requests with valid proxy token + valid role/user identity are authorized by RBAC policy.
- Existing cash and outputs transition workflows remain functional.

Non-functional:
- Authentication denials are logged with structured context.
- No secrets committed to repository.
- Docker path remains operational.

Quality gates:
- Test suite passes in Docker.
- QA sign-off published for Sprint 5 scope.

## Work Breakdown

1. Backend security integration (Sage)
- Implement proxy-token auth mode and error handling.
- Add tests for auth mode matrix.

2. UX and API shape hardening (Nova + Milo)
- Improve endpoint response consistency and error messages.
- Keep role-aware behavior explicit.

3. QA execution (Ivy)
- Validate auth mode matrix in runtime.
- Validate regressions on cash/outputs transitions.

4. Producer coordination (Remy)
- Track scope boundaries and merge readiness.
- Keep sprint artifacts synchronized.

## Definition of Done

- Sprint 5 scope merged to main.
- docs/sprint-5/progress.md reflects final status and evidence.
- docs/sprint-5/done.md completed with validation and residual risk notes.
- docs/qa/sprint-5-signoff.md published (or blocked with issue ids).
