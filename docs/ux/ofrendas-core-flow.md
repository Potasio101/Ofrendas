# Flow Specification - Ofrendas Core (Figma Ready)

## Entry Points

1. Dashboard Home
2. New Envelope
3. Cash Window
4. Day Log
5. Outputs
6. Kiosk
7. Summary/Reports

## Global Design Principles

1. Speed first on service day: primary actions visible above fold.
2. Audit by design: every edit path includes trace metadata.
3. Progressive disclosure: advanced options hidden until needed.
4. Role-aware UI: disable edit/approval actions for auditor.
5. Mobile-first touch targets and large typography.

## Screen Flow 1 - Envelope Capture

1. Home -> New Envelope
2. Upload/Camera -> OCR Result
3. User chooses:
   - Confirm now
   - Send to deferred review
4. Confirmation stores record and returns to Home.

Exit points:

- Success: envelope confirmed.
- Deferred: record enters review queue.
- Error: OCR failure, user retries upload.

## Screen Flow 2 - Day Log And Deferred Correction

1. Home -> Day Log
2. Filter by status/user/time
3. Open record detail
4. Edit one or more fields
5. Save with optional reason
6. Timeline updates immediately

Exit points:

- Success: review status moves to reviewed.
- Follow-up: status moves to needs_followup.

## Screen Flow 3 - Cash Window

1. Home -> Cash
2. Expected total displayed
3. Denomination table input
4. Counted total + variance auto-calculated
5. Save partial or close session

Exit points:

- Save partial: session remains open.
- Close: session locked, close event logged.

## Screen Flow 4 - Outputs

1. Home -> Outputs
2. Create output
3. Select fund source from catalog
4. Submit for approval
5. Admin approves or rejects

Exit points:

- Approved: status approved/paid.
- Rejected or needs edit: returns to draft/submitted.

## Screen Flow 5 - Fund Source Management

1. Outputs -> Manage Fund Sources
2. Add new source code + name
3. Activate/deactivate source
4. Historical records remain linked

Exit points:

- Source added and available immediately.
- Source deactivated but preserved in history.

## Screen Flow 6 - Kiosk POS

1. Home -> Kiosk
2. Add line items (catalog or custom line)
3. Set quantity and unit price
4. Select payment method
5. If zelle: search customer or create on the fly
6. Record payment and close ticket

Exit points:

- Paid: order status paid.
- Cancelled: order status cancelled.

## Screen Flow 7 - Export Configuration And Execution

1. Admin -> Exports
2. Upload CSV template
3. Confirm field mapping profile
4. Save profile version
5. Run export by period
6. Review status and generated file path

Exit points:

- Success: file generated and saved.
- Failure: status failed with errors.

## Key Components For Figma Library

1. Primary action card (Home module tile)
2. Audit timeline item
3. Denomination row editor
4. Fund source selector (active/inactive states)
5. Status chip set (draft/submitted/approved/paid/closed)
6. Payment method segmented control (cash/zelle)
7. Data table row with quick actions
8. Confirm modal with actor + timestamp preview

## Accessibility Requirements

### Keyboard Navigation

- All actions reachable by Tab.
- Logical focus order on forms and tables.
- Visible focus style for every control.

### Screen Reader Support

- Form labels must be explicit, not placeholder-only.
- Variance alerts and status changes announced.
- Timeline entries include actor and timestamp text.

### Visual Accessibility

- Minimum contrast ratio 4.5:1 for body text.
- Touch targets at least 44px height.
- Error states use color + icon + text.
- Support 200% text zoom without clipping.

## Figma Handoff Notes

1. Build mobile frames first, then tablet/desktop adaptations.
2. Prototype critical journeys:
   - capture -> deferred review -> close
   - outputs create -> approve
   - kiosk ticket -> zelle payment
3. Mark role-restricted controls with design annotations.
4. Include empty, loading, and failure states for each list page.
