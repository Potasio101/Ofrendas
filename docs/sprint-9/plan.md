# Sprint 9 Plan - Model Promotion, Rollback, and Ongoing Operations

Sprint window: 1 week
Branch: feature/sprint-9
Owner: Dev team (Nova/Sage/Milo)
QA owner: Ivy
Producer: Remy

## Sprint Goal

Enable safe model promotion and rollback with admin visibility, scheduled retraining, and production guardrails.

## In Scope

1. Promotion control plane
- Add model registry status (`candidate`, `active`, `archived`, `failed`).
- Add explicit promote endpoint restricted to admin.
- Add rollback endpoint to previous active model.

2. Promotion gates and safety checks
- Define minimum acceptance thresholds for promotion:
  - name match precision
  - amount parse accuracy
  - fallback reduction
- Block promotion if gates fail.

3. Scheduled ongoing training
- Add nightly scheduler trigger (configurable window).
- Add minimum sample threshold to skip low-value retrains.
- Add cooldown period between jobs.

4. Admin UX and runbook
- Show latest active model, latest candidate metrics, and recent job history.
- Show clear action logs for force, promote, rollback.
- Document operational runbook and incident steps.

## Out of Scope

- Multi-model traffic splitting by cohort.
- Cross-region model serving.
- Full BI dashboard integration.

## Related ADRs

- ADR-012: Ongoing Training with Admin Force Trigger and Safe Promotion.

## Work Breakdown

1. Backend (Sage)
- Implement model registry and promotion/rollback APIs.
- Implement threshold evaluator for gate checks.
- Add scheduler wiring and cooldown/threshold guards.

2. Frontend/UI (Nova + Milo)
- Extend admin page with model status and control actions.
- Add confirmation UX for promote and rollback.

3. QA (Ivy)
- Validate blocked promotion on failed thresholds.
- Validate rollback restores previous active model.
- Validate scheduler skip behavior under low sample volume.

4. Producer (Remy)
- Align business sign-off on thresholds.
- Ensure runbook is complete before release.

## Acceptance Criteria

Functional:
- Admin can promote only passing candidates.
- Admin can rollback to previous active model.
- Nightly retraining runs only when thresholds are met.

Non-functional:
- All control actions are audit-logged.
- Service continues operating if scheduled training fails.

Quality gates:
- Test suite passes in Docker.
- QA sign-off document published.

## Definition of Done

- Sprint 9 scope merged to main.
- `docs/sprint-9/progress.md` reflects final evidence.
- `docs/sprint-9/done.md` completed with risks and next inputs.
- `docs/qa/sprint-9-signoff.md` published (or blocked with issue ids).
