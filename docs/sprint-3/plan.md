# Sprint 3 Plan - Authentication Hardening and Module Expansion Start

Sprint window: 1 week
Branch: feature/sprint-3
Owner: Dev team (Nova/Sage/Milo)
QA owner: Ivy
Producer: Remy

## Sprint Goal

Move from header-based local identity to a safer authentication source pattern and start executable expansion for cash window and outputs modules.

## In Scope

1. Authentication source hardening
- Introduce trusted auth context abstraction (dev and non-dev paths).
- Restrict header-based identity to local/dev mode only.
- Add explicit configuration gates for auth mode selection.

2. RBAC integration tightening
- Keep endpoint policy map and denial logging from Sprint 2.
- Ensure auth source and role resolution feed policy checks consistently.
- Add negative tests for disallowed auth mode bypass paths.

3. Cash window module kickoff
- Add minimal domain/service/repository contracts for cash session open/close.
- Add first route stubs and persistence wiring for session lifecycle.
- Keep denomination counting deep workflow out of scope for this sprint.

4. Outputs module kickoff
- Add minimal contracts for output draft registration with fund source.
- Add first route/service skeleton for creating and listing output drafts.
- Keep full approval workflow out of scope for this sprint.

5. Test and QA baseline
- Add tests for auth mode behavior and role resolution.
- Add tests for cash window and outputs skeleton paths.
- Publish QA sign-off with auth mode and role matrix checks.

## Out of Scope

- Full external identity provider integration.
- Full cash counting and reconciliation workflow.
- Full outputs approval and settlement workflow.
- Export provider implementation.

## Acceptance Criteria

Functional:
- App enforces configured auth source behavior without silent fallback in non-local mode.
- Existing protected routes continue honoring RBAC decisions.
- Cash window and outputs modules expose first working route/service skeletons.
- New skeleton endpoints are covered by tests and return deterministic responses.

Non-functional:
- Security-relevant auth decisions are logged.
- No hardcoded credentials or secret leakage in repository.
- Docker run path remains operational.

Quality gates:
- Unit/integration tests pass in Docker.
- QA playthrough completed and documented.

## Work Breakdown

1. Backend hardening (Sage)
- Implement auth source abstraction and mode gating.
- Add module skeleton services/repositories/routes.

2. Frontend and UX (Nova + Milo)
- Add initial screens/actions for cash window and outputs drafts.
- Keep role-aware visibility aligned with RBAC policy.

3. QA execution (Ivy)
- Validate auth mode behavior and role matrix.
- Validate module skeleton happy path and deny path.

4. Producer coordination (Remy)
- Track scope boundaries and merge readiness.
- Keep progress artifacts updated continuously.

## Definition of Done

- Sprint 3 scope merged to main.
- docs/sprint-3/progress.md updated with final status and issue references.
- docs/sprint-3/done.md completed with validation evidence and residual risks.
- QA sign-off note created (or explicit blocked status with issue ids).
