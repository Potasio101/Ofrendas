# Brainstorm 001 - Ofrendas Build Kickoff

Date: 2026-05-08
Facilitator: Remy (Producer)
Participants: Nova (Frontend), Sage (Backend), Milo (Visual), Ivy (QA), Dash (DevOps)

## Prompt Used

How should we execute Sprint 1 to deliver the first usable vertical slice fast, with auditability from day one, while keeping infra cost near zero?

## Agent Positions

Remy (Producer):
- Keep sprint scope narrow: capture -> review -> confirm -> day summary.
- Defer kiosk and outputs implementation to later sprint unless blockers are found.
- Require explicit acceptance criteria per endpoint and role.

Nova (Frontend):
- Build day-log deferred correction in Sprint 1, not later.
- Without it, treasurer workflow is unrealistic on service day.
- Prioritize touch-target size and fast keyboard flows over polish.

Sage (Backend):
- Implement migration-backed domain slices first: offerings, review queue, field history.
- Add cash and outputs tables in API only after core envelope loop passes tests.
- Keep strategy interfaces real from day one to avoid rewrite.

Milo (Visual):
- Do a minimal but intentional UI system now (type scale, spacing, contrast tokens).
- If skipped, accessibility debt will multiply and slow future screens.
- Do not ship dense table-only layouts for mobile operators.

Ivy (QA):
- Add audit assertions in automated tests immediately.
- A working form without history validation is a release blocker.
- Create a deterministic sample data fixture for service-day flows.

Dash (DevOps):
- Use Docker Compose from day one for parity.
- Add health/readiness and structured logs in first increment.
- Cloudflare Tunnel setup can remain documented until first remote pilot.

## Real Disagreements

Disagreement 1:
- Nova wants deferred correction in Sprint 1.
- Remy proposes deferring to Sprint 2 for speed.
- Resolution: include a thin deferred correction path in Sprint 1 (view + save + field audit), no advanced filtering yet.

Disagreement 2:
- Sage wants to postpone observability to Sprint 2.
- Dash insists health/readiness and basic structured logs are mandatory in Sprint 1.
- Resolution: include minimal observability baseline in Sprint 1 definition of done.

## Decisions

1. Sprint 1 includes full core envelope vertical slice plus thin deferred correction.
2. Sprint 1 includes health/readiness endpoints and structured logging baseline.
3. Sprint 1 excludes kiosk POS and outputs UI, but keeps schema awareness and routing stubs if needed.
4. QA sign-off requires at least one end-to-end flow with audit evidence checks.

## Risks and Mitigations

Risk: OCR quality too low for real capture speed.
Mitigation: allow immediate manual correction with confidence display and keep OCR swappable.

Risk: migration mismatch with repository layer.
Mitigation: add migration smoke test in CI and fixture-based integration test.

Risk: user confusion during busy service hours.
Mitigation: mobile-first forms, large inputs, explicit Confirm vs Send to Review actions.
