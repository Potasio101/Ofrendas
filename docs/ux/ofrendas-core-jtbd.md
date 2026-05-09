# JTBD - Ofrendas Core Operations

## Scope

This document defines Jobs-to-be-Done for the core app operations:

- envelope capture and correction
- cash window
- disbursements (outputs)
- kiosk POS
- accounting exports

## Primary Personas

- Treasurer: Operates capture and daily finance workflow, mostly on mobile.
- Admin: Approves sensitive actions, configures fund sources and exports.
- Auditor: Reviews records and traceability in read-only mode.

## Job Statement 1 - Envelope Capture

When I am processing envelopes quickly during service,
I want to capture and confirm them with OCR support,
so I can finish intake without losing data quality.

### Current Pain Points

- Manual data entry is slow.
- Real-time correction pressure causes mistakes.
- Missing audit trail creates reconciliation stress.

### Desired Outcomes

- Fast capture in under 30 seconds per envelope.
- Deferred correction available after rush periods.
- Every field change is traceable.

## Job Statement 2 - Cash Control

When I am closing the day,
I want to count denominations and compare expected vs counted cash,
so I can detect differences immediately and close with accountability.

### Current Pain Points

- Mixed notes and manual totals.
- No standardized close process.
- Discrepancies discovered too late.

### Desired Outcomes

- Single cash window with denomination breakdown.
- Explicit variance at close.
- Recorded close actor and timestamp.

## Job Statement 3 - Outputs/Disbursements

When money leaves the church for expenses or aid,
I want each output recorded with category, source fund, and approval,
so finances remain auditable and policy-compliant.

### Current Pain Points

- Outputs tracked informally.
- Fund source is ambiguous.
- Approval ownership is unclear.

### Desired Outcomes

- Fund source chosen from extensible catalog.
- Approval workflow by role.
- Reports grouped by source fund.

## Job Statement 4 - Kiosk POS

When we sell food at the church kiosk,
I want to create simple tickets with quantity, item, and payment method,
so we can track sales and payments without a separate system.

### Current Pain Points

- Sales tracked manually.
- Zelle customer names are inconsistent.
- No consolidated sales history.

### Desired Outcomes

- Fast POS flow for cash and zelle.
- Reuse existing customer or create on the fly.
- Same-day sales traceability.

## Job Statement 5 - Accounting Export

When accounting requests data in specific formats,
I want configurable export profiles from uploaded CSV templates,
so we can adapt quickly without code changes.

### Current Pain Points

- Provider formats change.
- Hardcoded exports create maintenance overhead.

### Desired Outcomes

- Admin-configurable mapping profiles.
- Versioned export templates.
- Export audit status retained.

## Constraints

- Low budget, self-hosted preference.
- Linux + Docker + M365 stack.
- Operational days: Tuesday, Thursday, Sunday.
- Mobile-first usability is mandatory.

## Success Metrics

- Envelope processing completion on service days with <3% post-correction rate.
- Cash close completed same day with variance recorded 100% of time.
- 100% outputs linked to fund source and approver.
- Kiosk sales recorded with payment method for 100% tickets.
- Export profile changes performed without deployments.
