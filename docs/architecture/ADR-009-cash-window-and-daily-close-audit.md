# ADR-009: Cash Window with Daily Close and Audit Trail

- Status: Accepted
- Date: 2026-05-08

## Context

Treasurer needs a dedicated cash window to count physical money by denomination, compare against expected cash total, and close the day with traceability.

## Decision Drivers

- Improve operational control for cash handling.
- Detect discrepancies early (variance at close).
- Preserve audit evidence for all cash adjustments.

## Options Considered

1. Record only a single daily cash total without denomination details.
2. Track denomination-level counting in UI without persistent event history.
3. Track denomination-level counting with auditable session lifecycle.

## Decision

Choose option 3.

- Add `GET /cash`, `POST /cash/save`, and `POST /cash/close` UI flows.
- Persist one cash session per service date.
- Store denomination lines and all relevant cash events.
- Limit open/close permissions to treasurer and admin roles.

## Rationale

Denomination-level tracking improves accuracy and allows strong audit review when differences appear.

## Consequences

- Positive:
  - Better visibility of expected vs counted cash.
  - Clear accountability for who opened/closed and edited lines.
  - Consistent daily closing procedure.
- Negative:
  - Additional UI and process steps for operators.
  - Requires user training on denomination workflow.

## Implementation Notes

- Recalculate line totals and session variance on each save.
- Require optional note when closing with non-zero variance.
- Expose read-only cash timeline for auditor role.