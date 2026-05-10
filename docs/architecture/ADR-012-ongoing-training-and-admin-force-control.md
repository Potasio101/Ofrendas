# ADR-012: Ongoing Training with Admin Force Trigger and Safe Promotion

- Status: Accepted
- Date: 2026-05-09

## Context

OCR and correction quality must improve over time from real operator corrections. The team requested a Force Training action in admin to run model updates on demand, while keeping capture operations stable.

## Decision Drivers

- Improve OCR correction quality continuously.
- Avoid blocking request-time capture flows during training.
- Keep strong control and auditability for manual force runs.
- Prevent unsafe model activation without quality checks.
- Keep architecture operable by a small team.

## Options Considered

1. Retrain synchronously from admin click in web request thread.
2. Retrain asynchronously with job queue and force trigger endpoint.
3. Retrain only on fixed nightly schedule with no manual trigger.

## Decision

Choose option 2.

- Use asynchronous training jobs with explicit states (`queued`, `running`, `succeeded`, `failed`, `canceled`).
- Add admin-only Force Training endpoint and UI action.
- Enforce single active training job via lock.
- Keep training separate from promotion.
- Promote candidate model only when quality gates pass.
- Provide explicit rollback to previous active model.

## Rationale

This balances operational safety and iteration speed. Manual force runs are available when needed, but model changes are still controlled by objective quality gates.

## Consequences

- Positive:
  - Faster improvement loop from real corrections.
  - Better operability with clear job status and logs.
  - Safer releases through promote/rollback controls.
- Negative:
  - Additional complexity (job orchestration, registry, control endpoints).
  - Requires clear runbook and monitoring discipline.

## Implementation Notes

- Persist full training labels (`raw_ocr`, `corrected`, field, confidence, actor, timestamp).
- Restrict force/promotion/rollback to admin role.
- Audit log all control actions with actor and request context.
- Add scheduler for nightly run with minimum-sample threshold and cooldown.
- Do not block capture routes while training is active.
