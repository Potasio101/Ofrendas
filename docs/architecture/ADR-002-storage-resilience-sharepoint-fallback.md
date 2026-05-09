# ADR-002: PostgreSQL as Primary Operational Storage (SharePoint Deferred)

- Status: Accepted
- Date: 2026-05-08

## Context

The team needs a simpler MVP with one operational datastore. SharePoint is not required for daily data visibility because the app itself provides the necessary views and reports.

## Decision Drivers

- Reduce implementation complexity in MVP.
- Keep one clear source-of-truth for transactional data.
- Improve reliability by avoiding cross-system sync in phase 1.
- Preserve future optional integration path for exports.

## Options Considered

1. SharePoint + PostgreSQL dual persistence from day one.
2. PostgreSQL-only for operational data in MVP.
3. SharePoint-only with app-level reporting overlays.

## Decision

Choose option 2.

- Canonical operational writes: PostgreSQL.
- App reads/reports: PostgreSQL.
- No mandatory SharePoint sync in phase 1.
- SharePoint export integration remains a future optional capability.

## Rationale

This minimizes delivery risk and removes unnecessary operational coupling while preserving future extensibility.

## Consequences

- Positive:
  - Faster delivery and simpler maintenance.
  - Fewer consistency and reconciliation failure modes.
  - Clearer operational ownership for data.
- Negative:
  - Institutional SharePoint workflows are postponed.
  - Future SharePoint export requires a dedicated integration phase.

## Implementation Notes

- Keep migration discipline in PostgreSQL as the single operational record.
- Remove mandatory SharePoint fallback/sync requirements from MVP runbooks.
- Design export interfaces so a future SharePoint adapter can be added without changing core domain logic.