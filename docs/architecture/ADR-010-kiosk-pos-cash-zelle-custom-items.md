# ADR-010: Kiosk POS Mode with Cash/Zelle and Custom Items

- Status: Accepted
- Date: 2026-05-08

## Context

The church has a small food kiosk requiring quick sales capture from the same app. Payments are usually cash or zelle, and operators need to create custom items directly from UI.

## Decision Drivers

- Keep kiosk workflow simple and fast.
- Reuse existing app security/audit model.
- Support zelle payer tracking with lookup and auto-create.
- Avoid code changes for frequent item/menu updates.

## Options Considered

1. External POS tool disconnected from offerings app.
2. Basic table-only capture without item catalog.
3. Integrated kiosk POS module with catalog, custom lines, and payment tracking.

## Decision

Choose option 3.

- Add dedicated kiosk routes and screens.
- Store catalog items plus ad-hoc custom line items.
- Support `cash` and `zelle` payment methods.
- For zelle payments, reuse existing customer when found; create new customer when not found.

## Rationale

Integrated flow reduces operational friction and keeps audit and reporting centralized.

## Consequences

- Positive:
  - Unified reporting across offerings and kiosk activity.
  - Faster operator workflow with less context switching.
  - Better accountability through user and event tracking.
- Negative:
  - Additional module complexity in UI and data model.
  - Requires staff training for kiosk process.

## Implementation Notes

- Enforce non-zero totals before payment closure.
- Require payer name for zelle payments.
- Track all item creation and payment events in audit/event tables.
- Restrict create/edit actions to treasurer and admin roles.