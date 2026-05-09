# Sprint 6 Done Handoff

Status: Completed on feature branch, pending merge to main

## What Was Delivered

- Added `proxy-signed` auth mode with HMAC signature validation.
- Added freshness validation via `X-Proxy-Timestamp` and max-age config.
- Kept prior auth modes (`local-dev`, `header-strict`, `proxy-token`) unchanged.
- Added mobile-first workflow pages:
	- `GET /workflow/cash`
	- `GET /workflow/outputs`
- Added tests for signed proxy auth success/failure paths.
- Added tests validating workflow pages render for allowed role.

## Validation Summary

- Docker build and test run executed successfully.
- Test result: `42 passed`.
- Validation command:
	- `docker compose build app && docker compose run --rm app python -m pytest -q`

## Issues Found and Resolved

- Fixed `proxy-signed` test setup by providing signing secret in test config.
- Fixed workflow pages route registration bug caused by accidental nested route definitions.

## Remaining Risks

- Workflow pages are intentionally minimal and should evolve to richer task UX in a future sprint.
- Signed proxy mode currently assumes a shared symmetric secret; key rotation process should be documented in ops runbook.

## Next Sprint Inputs

- Add richer workflow actions from UI for outputs submit/approve/pay with visible state history.
- Add stronger audit/event visibility in UI for cash and outputs transitions.
- Define and document secret rotation policy for signed proxy identity mode.

## Handoff Commands

Read PROJECT_BRIEF.md and docs/sprint-6/progress.md.
Continue from unresolved tasks and open issues.
