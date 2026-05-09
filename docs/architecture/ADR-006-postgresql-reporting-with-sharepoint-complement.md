# ADR-006: PostgreSQL as Single Source of Truth for App Operations and Reporting

- Status: Accepted
- Date: 2026-05-08

## Context

The app needs fast in-app reporting, filtering, and operational consistency with minimal architecture complexity in MVP.

## Decision Drivers

- Keep one source-of-truth for operational data.
- Enable efficient queryable reporting.
- Reduce sync/reconciliation overhead in phase 1.
- Preserve optional export extensibility for future integrations.

## Options Considered

1. SharePoint-only storage and reporting.
2. PostgreSQL-only storage and reporting.
3. PostgreSQL for app operations with mandatory SharePoint complement.

## Decision

Choose option 2.

- PostgreSQL is the source-of-truth for app writes and reads.
- Reports and analytics queries run against PostgreSQL.
- SharePoint is not an active persistence dependency in phase 1.
- Future SharePoint export can be added as an optional adapter.

## Rationale

A single-store model improves delivery speed, operational clarity, and data consistency for the current phase.

## Consequences

- Positive:
  - Better report performance and filtering capabilities.
  - Lower operational complexity.
  - Clear ownership of transactional consistency.
- Negative:
  - SharePoint institutional export workflows are deferred.
  - A later integration phase is needed for SharePoint export.

## Implementation Notes

- Use schema migrations for PostgreSQL changes.
- Keep source-of-truth rules simple: operational datasets are owned by PostgreSQL.
- Ensure export contracts are storage-agnostic to support future adapters.