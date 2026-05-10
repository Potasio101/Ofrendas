# ADR-012: OCR Debug Runtime Toggle with Admin-Controlled Artifact Observability

Status: Accepted  
Date: 2026-05-10  
Deciders: Dev team + QA + Producer

## Context

OCR extraction failures require fast, evidence-based troubleshooting. Current flow lacks request-level observability to diagnose segmentation/ROI issues against real envelope captures.

Operational need:
- Enable/disable debug collection at runtime without restart.
- Keep debug data admin-only.
- Preserve reliability: debug failures must not block `/process`.
- Limit storage growth with retention and max-session controls.

## Decision

Implement an admin-controlled OCR debug runtime service with:

1. Runtime controls
- `OCR_DEBUG_ENABLED=false` default.
- `OCR_DEBUG_RETENTION_DAYS=7`.
- `OCR_DEBUG_MAX_SESSIONS=500`.
- Admin endpoints to read status and toggle ON/OFF.

2. Artifact model per request
- Store under `/app/data/ocr-debug/<request_id>/`.
- Save input, preprocessed image, key ROI crops, raw OCR payload, parsed fields, timings, and metadata.

3. Safety and resilience
- Any debug-write failure logs structured event `ocr_debug_write_failed` with request id.
- OCR processing result path remains successful even when debug write fails.
- Access restricted to admin RBAC policy.

4. Storage hygiene
- Retention cleanup by age and max-session trimming to cap disk usage.

## Decision Drivers

- Faster root-cause analysis for OCR misses.
- Runtime operability for service-day incidents.
- Predictable storage costs.
- Preserve auditability without exposing sensitive routes to non-admin roles.

## Options Considered

1. Always-on debug artifacts
- Pros: complete trace.
- Cons: high storage growth and unnecessary overhead in normal operations.

2. Runtime admin toggle (selected)
- Pros: targeted capture during incidents, lower cost, safer default OFF.
- Cons: incidents before toggle activation may miss traces.

3. External observability platform only
- Pros: centralized analytics.
- Cons: added operational cost and integration complexity for current scope.

## Consequences

Positive:
- Immediate troubleshooting visibility for OCR pipeline behavior.
- Admin UX now supports direct incident triage.
- Controlled storage footprint via retention policies.

Trade-offs:
- Local filesystem artifacts require future strategy for clustered deployments.
- Admin discipline needed to disable debug after incident windows.

## Security

- OCR debug endpoints are admin-only via existing RBAC checks.
- No auth tokens/secrets are logged by debug pipeline.
- Artifacts remain on server-side path and are accessed only through admin routes.

## Operational Notes

- Keep debug disabled by default in production.
- Enable temporarily during OCR incident windows.
- Monitor disk usage of `/app/data/ocr-debug`.
- Periodically review retained sessions for support runbook updates.
