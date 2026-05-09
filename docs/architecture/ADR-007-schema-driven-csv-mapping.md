# ADR-007: Schema-Driven CSV Mapping for Accounting Exports

- Status: Accepted
- Date: 2026-05-08

## Context

Accounting tools use different import layouts. Hardcoding exporter fields per provider does not scale and increases maintenance cost.

## Decision Drivers

- Minimize code changes when accounting formats change.
- Let admin configure mappings without developer intervention.
- Keep export behavior auditable and versioned.
- Preserve compatibility with configurable file delivery destinations.

## Options Considered

1. Hardcoded mappings per provider in Python code.
2. Config files in repository managed by developers.
3. Schema-driven mapping via uploaded CSV templates and persisted mappings.

## Decision

Choose option 3.

- Admin uploads a CSV template from target accounting software.
- System parses headers and stores template metadata.
- Mapping profile links canonical fields to target columns.
- Export jobs use active profile per provider/version.

## Rationale

This provides flexibility for non-technical administrators while keeping governance through profile versioning and audit logs.

## Consequences

- Positive:
  - Faster onboarding of new accounting formats.
  - Reduced deployment churn for mapping-only changes.
  - Clear traceability of which mapping profile produced each export.
- Negative:
  - Requires robust validation UI and guardrails.
  - Incorrect mappings can cause accounting import errors.

## Implementation Notes

- Validate required canonical fields before profile activation.
- Support profile versioning with rollback to previous active version.
- Save uploaded template files and parse results for audit.
- Restrict profile management to admin role.