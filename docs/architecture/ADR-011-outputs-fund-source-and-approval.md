# ADR-011: Outputs Control with Fund Source and Approval Audit

- Status: Accepted
- Date: 2026-05-08

## Context

The church periodically needs to disburse money for operational expenses and benevolence. These outputs usually come from offerings, while tithe policy may differ and is still being finalized.

## Decision Drivers

- Keep complete audit trail for every output.
- Distinguish origin fund (offering, tithe, other).
- Support approval workflow for governance.
- Preserve policy flexibility while finance rules are refined.

## Options Considered

1. Track outputs as free-text notes without structure.
2. Track outputs as generic cash events without fund source.
3. Dedicated disbursement module with fund source and approval states.

## Decision

Choose option 3.

- Add output records with category, amount, beneficiary, and fund source.
- Keep `fund_source` as an extensible catalog (not hardcoded enum in app logic).
- Add status workflow (`draft`, `submitted`, `approved`, `paid`, `void`).
- Require approver user for approval steps.
- Keep tithe handling configurable with optional extra justification.

## Rationale

This provides financial traceability without blocking current operations while fund governance matures.

## Consequences

- Positive:
  - Stronger auditability and accountability.
  - Clear reporting by source fund and category.
  - Flexible handling of tithe-related policy updates.
- Negative:
  - More process steps for operators.
  - Requires role and approval discipline.

## Implementation Notes

- Default source fund for operational expenses: `offering`.
- Add reporting views grouped by `fund_source_code`.
- Restrict approval action to admin role (recommended baseline).
- Allow add/deactivate fund sources from admin UI without schema changes.
- Do not delete fund sources used by historical records; mark inactive instead.