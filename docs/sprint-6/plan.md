# Sprint 6 Plan - Proxy Signed Identity and Workflow UI Foundations

Sprint window: 1 week
Branch: feature/sprint-6
Owner: Dev team (Nova/Sage/Milo)
QA owner: Ivy
Producer: Remy

## Sprint Goal

Add a stronger non-local identity validation mode using signed proxy headers and ship first workflow UI views for cash and outputs operations.

## In Scope

1. Signed proxy identity mode
- Add `proxy-signed` auth mode in app auth pipeline.
- Validate signature over identity headers and timestamp with shared secret.
- Enforce replay window validation using configurable max age.

2. Auth hardening behavior
- Keep existing `local-dev`, `header-strict`, and `proxy-token` modes.
- Add deterministic error reasons for missing signature, stale timestamp, and invalid signature.
- Keep RBAC policy checks unchanged and downstream-compatible.

3. Workflow UI foundation
- Add basic HTML views for cash workflow actions (open/line/close/reopen).
- Add basic HTML views for outputs transitions (draft/submit/approve/pay).
- Keep API endpoints as source of truth; UI posts to existing routes.

4. Test and QA baseline
- Add tests for signed-proxy auth mode success and failure paths.
- Run smoke checks for signed mode and workflow views.
- Publish QA sign-off artifact for sprint scope.

## Out of Scope

- Full OIDC redirect flow with session cookies.
- Multi-factor authentication.
- Rich design system for workflow UI.

## Acceptance Criteria

Functional:
- `proxy-signed` mode accepts only valid signatures in allowed freshness window.
- Invalid signature and stale requests are denied with 401.
- Cash and outputs workflow pages render and submit actions successfully for allowed roles.

Non-functional:
- Auth failure reasons are logged in structured form.
- Test suite passes in Docker.
- Existing routes remain backward compatible.

Quality gates:
- Automated tests pass in Docker.
- QA sign-off published for Sprint 6 scope.

## Definition of Done

- Sprint 6 scope merged to main.
- docs/sprint-6/progress.md reflects final evidence.
- docs/sprint-6/done.md completed with risks and next inputs.
- docs/qa/sprint-6-signoff.md published (or blocked with issue ids).
