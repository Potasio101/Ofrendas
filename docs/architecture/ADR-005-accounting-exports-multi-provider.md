# ADR-005: Multi-Provider Accounting Export Architecture

- Status: Accepted
- Date: 2026-05-08

## Context

The project needs to export offering data to accounting systems, starting with QuickBooks and expanding to other major providers without rewriting business logic.

## Decision Drivers

- Avoid vendor lock-in.
- Keep export logic separated from core offering processing.
- Support file-based workflows used by church administrative teams.
- Maintain auditability of every export run.

## Options Considered

1. One hardcoded QuickBooks exporter in service layer.
2. Strategy-based export module per provider.
3. Third-party iPaaS integration from day one.

## Decision

Choose option 2.

- Introduce `IExportStrategy` and concrete implementations per provider.
- Start with `QuickBooksExportStrategy` and `GenericCsvExportStrategy`.
- Add Xero/Zoho/Sage strategies incrementally.
- Use configurable export destinations (local filesystem in MVP; SharePoint adapter optional in future).

## Rationale

This aligns with existing SOLID/Strategy design and allows progressive integration as requirements evolve.

## Consequences

- Positive:
  - Clean extension model for new providers.
  - Better separation of concerns.
  - Reusable canonical export dataset.
- Negative:
  - Requires mapping maintenance per provider.
  - Validation/testing matrix grows with each exporter.

## Implementation Notes

- Record export audit trail: period, provider, destination path, row count, status.
- Use idempotent export IDs to avoid duplicate imports.
- Keep provider-specific templates in versioned configuration.