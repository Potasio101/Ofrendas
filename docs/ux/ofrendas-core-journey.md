# User Journey - Ofrendas Core Workflow

## Persona

- Who: Church Treasurer
- Goal: Capture envelopes, reconcile cash, and finish auditable daily close.
- Context: Service day operations under time pressure, mostly on mobile.
- Success Metric: No missing records, cash closed, outputs approved, traceability complete.

## Stage 1 - Start Of Day

What user is doing:

- Opens app and checks pending tasks.

What user is thinking:

- I need a clean start and quick access to key actions.

What user is feeling:

- Focused, slightly rushed.

Pain points:

- Too many entry points if dashboard is not clear.

Opportunity:

- Dashboard with three primary actions: New Envelope, Cash Window, Day Log.

## Stage 2 - Envelope Intake Rush

What user is doing:

- Uploads photo, reviews OCR output, confirms quickly.

What user is thinking:

- I should not get blocked by perfect correction now.

What user is feeling:

- Time pressure.

Pain points:

- OCR uncertainty on names and amounts.

Opportunity:

- One-tap confirm with later correction queue.

## Stage 3 - Deferred Correction

What user is doing:

- Opens day log and reopens unresolved entries.

What user is thinking:

- I can fix this calmly now and keep an audit trail.

What user is feeling:

- More confident.

Pain points:

- Risk of losing track of what changed.

Opportunity:

- Field timeline: old value, new value, actor, timestamp, reason.

## Stage 4 - Cash Reconciliation

What user is doing:

- Counts denominations and compares expected vs counted cash.

What user is thinking:

- I need to close cash with zero surprises.

What user is feeling:

- Cautious.

Pain points:

- Manual calculators and inconsistency.

Opportunity:

- Live variance calculation and explicit close confirmation.

## Stage 5 - Outputs And Approvals

What user is doing:

- Creates outputs for payments/aid and submits for approval.

What user is thinking:

- This must be tied to the right fund source.

What user is feeling:

- Accountable.

Pain points:

- Unclear governance if source fund is free text.

Opportunity:

- Fund source catalog + role-based approval flow.

## Stage 6 - Kiosk Sales (If Active)

What user is doing:

- Creates ticket, records cash/zelle payment, closes sale.

What user is thinking:

- Keep this fast, but track payer correctly.

What user is feeling:

- Fast-paced, transactional.

Pain points:

- New zelle payers not in list.

Opportunity:

- Search-or-create payer in one flow.

## Stage 7 - End Of Day Audit Readiness

What user is doing:

- Reviews summary and confirms all modules are reconciled.

What user is thinking:

- If auditor asks, all evidence must be ready.

What user is feeling:

- Relief when all statuses are closed.

Success criteria:

- No unresolved critical records.
- Cash close recorded with variance and actor.
- Outputs have source fund and approval data.
- All significant actions have immutable logs.
