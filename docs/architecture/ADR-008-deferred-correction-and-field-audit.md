# ADR-008: Deferred Correction Workflow and Field-Level Audit in UI

- Status: Accepted
- Date: 2026-05-08

## Context

Treasurer may capture envelopes quickly during service and correct uncertain fields later the same day. The system must preserve full auditability for every change.

## Decision Drivers

- Support real operational workflow under time pressure.
- Ensure every post-capture edit is traceable.
- Allow auditors to inspect history without edit permissions.

## Options Considered

1. Force correction only during immediate capture.
2. Allow deferred correction without detailed field history.
3. Allow deferred correction with review queue and field-level history.

## Decision

Choose option 3.

- Add day-log UI list for same-day entries.
- Allow reopening an entry for deferred corrections.
- Store every field change with old/new values, actor, timestamp, and reason.
- Restrict deferred correction actions to treasurer/admin roles.

## Rationale

This preserves operational speed while meeting audit requirements.

## Consequences

- Positive:
  - Better usability during high-paced capture windows.
  - Strong evidence trail for financial review.
  - Improved accountability by role.
- Negative:
  - Additional UI and storage complexity.
  - Requires careful permissions enforcement.

## Implementation Notes

- Introduce review queue status per offering.
- Add dedicated field history table for immutable change log.
- Expose read-only history timeline in auditor view.