# Sprint 4 Plan - Cash Window Full Flow and Outputs Approval Workflow

Sprint window: 1 week
Branch: feature/sprint-4
Owner: Dev team (Nova/Sage/Milo)
QA owner: Ivy
Producer: Remy

## Sprint Goal

Promote cash window and outputs from skeleton endpoints to end-to-end operational workflows with approval transitions and auditable events.

## In Scope

1. Cash window workflow completion
- Implement denomination line upsert and recalculation.
- Implement close session with variance calculation and event write.
- Implement reopen session control for admin role.

2. Outputs approval workflow completion
- Implement draft update and submit transition.
- Implement approve and paid transitions with role constraints.
- Enforce status transition rules and event logging per transition.

3. Route and service hardening
- Add explicit validation errors for invalid payload/state transitions.
- Keep RBAC policy alignment for treasurer/admin/auditor actions.
- Preserve existing auth mode behavior from Sprint 3.

4. Test and QA baseline
- Add unit/integration tests for cash session transitions and calculations.
- Add tests for outputs state machine and deny paths.
- Execute runtime smoke flow for both modules under role matrix.

## Out of Scope

- External accounting export workflow implementation.
- Advanced reporting/dashboard features.
- Identity provider integration beyond current auth mode abstraction.

## Acceptance Criteria

Functional:
- Cash session can be opened, updated with count lines, closed, and reopened under allowed roles.
- Disbursement can progress draft -> submitted -> approved -> paid with enforced transitions.
- Unauthorized role actions return 403 and do not mutate state.
- Invalid transitions return deterministic 4xx errors with no side effects.

Non-functional:
- Every state transition writes corresponding audit event rows.
- Health/readiness remain stable.
- Docker run path remains operational.

Quality gates:
- Test suite passes in Docker.
- QA sign-off published for Sprint 4 scope.

## Work Breakdown

1. Backend workflow implementation (Sage)
- Cash line and session state transitions.
- Outputs transition logic and repository updates.

2. Frontend and UX updates (Nova + Milo)
- Minimal workflow controls for close/reopen and approval transitions.
- Maintain role-aware visibility and safe defaults.

3. QA execution (Ivy)
- Role matrix and transition matrix validation.
- Event/audit persistence verification.

4. Producer coordination (Remy)
- Scope guardrail and merge readiness.
- Continuous updates in progress tracker.

## Definition of Done

- Sprint 4 scope merged to main.
- docs/sprint-4/progress.md reflects final status and evidence.
- docs/sprint-4/done.md completed with validation and residual risk notes.
- docs/qa/sprint-4-signoff.md published (or blocked with issue ids).
