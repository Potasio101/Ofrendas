# PROJECT_BRIEF

## 1. Project Overview

Ofrendas is a church operations app to digitize envelopes, run daily cash control, manage kiosk POS sales, and track outputs/disbursements with full auditability.

Current scope (May 2026):
- PostgreSQL is the operational source of truth.
- In-app reporting is required for daily finance workflows.
- SharePoint is out of scope for phase 1 and remains an optional future export target.

Primary users:
- Treasurer (capture, corrections, cash close, outputs draft)
- Admin (configuration, approvals, fund source catalog)
- Auditor (read-only traceability and reports)

## 2. Concept / Product Description

The product optimizes service-day speed while preserving audit evidence.

Core concept:
- Capture envelope image quickly.
- Use OCR + correction strategies to prefill fields.
- Confirm now or defer correction to day log queue.
- Keep immutable field history for post-capture edits.
- Control cash by denomination and enforce daily close traceability.
- Register kiosk sales (cash and zelle) including custom line items.
- Register outputs by configurable fund source and approval flow.

Design principles:
- Speed first during active service windows.
- Audit by design in every edit path.
- Progressive disclosure for advanced controls.
- Role-aware actions and permissions.

## 3. Tech Stack

Application:
- Python 3.11+
- Flask (web app)
- Gunicorn (production WSGI)
- APScheduler (background scheduled jobs)

Data and storage:
- PostgreSQL 15+ (primary transactional and reporting store)
- Local file storage for optional export artifacts in MVP

Processing:
- OpenCV for image cleanup and field cropping
- EasyOCR as initial OCR strategy
- Fuzzy matching as initial correction strategy

Operations:
- Docker and Docker Compose (recommended local/prod parity)
- Cloudflare Tunnel for low-cost secure ingress in production

## 4. Architecture (ASCII diagram)

```text
Mobile/User UI
   |
   v
Flask Routes (ui/app.py)
   |
   v
OfferingService + Domain Services
   |-- ImageProcessor (OpenCV)
   |-- OCRStrategy (EasyOCR now, swappable)
   |-- CorrectionStrategy (Fuzzy now, swappable)
   |-- Repositories
         |-- PostgreSQLRepo (source of truth)
         |-- TrainingRepo (local training metadata)
         |-- LocalExportRepo (optional export artifacts)

PostgreSQL
   |-- offerings, audit tables, review queue, field history
   |-- cash sessions + denomination lines + events
   |-- kiosk orders + payments + customer refs
   |-- outputs + fund_sources + approval events
   |-- export runs + mapping profile metadata

Scheduled jobs (separate process)
   |-- training job
   |-- export reconciliation
```

## 5. Key Files Map

Top-level:
- Ofrenda.md: consolidated architecture and implementation runbook
- README.md: scope summary and links
- db/migrations/*.sql: schema evolution
- docs/architecture/*.md: ADR set
- docs/ux/*.md: JTBD, journey, flow

New orchestration docs:
- PROJECT_BRIEF.md: cross-chat source of truth
- docs/brainstorm/brainstorm-001.md: initial team debate record
- docs/sprint-1/plan.md: sprint tasks and acceptance criteria
- docs/sprint-1/progress.md: live tracker for context recovery
- docs/sprint-1/done.md: sprint closure handoff
- docs/sprint-2/plan.md: sprint tasks and acceptance criteria
- docs/sprint-2/progress.md: live tracker for context recovery
- docs/sprint-2/done.md: sprint closure handoff
- docs/sprint-3/plan.md: sprint tasks and acceptance criteria
- docs/sprint-3/progress.md: live tracker for context recovery
- docs/sprint-3/done.md: sprint closure handoff
- docs/sprint-4/plan.md: sprint tasks and acceptance criteria
- docs/sprint-4/progress.md: live tracker for context recovery
- docs/sprint-4/done.md: sprint closure handoff

## 6. Team Roles

Producer (Remy):
- Scope control, sprint planning, issue triage, merge coordination
- Must not write application code

Dev Team:
- Nova (frontend): Flask UI templates, role-aware UX, forms and flows
- Sage (backend): services, repositories, API/routes, migrations integration
- Milo (visual): visual consistency, touch-first accessibility and readability

QA Team:
- Ivy (QA): end-to-end playthrough, bug filing, sign-off artifact per sprint

DevOps (Dash, on demand):
- Docker runtime, Cloudflare tunnel ops, deployment and health checks

## 7. Sprint Status (updated every sprint)

Current sprint: Sprint 4 (Cash window full flow and outputs approvals)
Status: In progress
Branch target: feature/sprint-4
Start criteria:
- Sprint 4 plan and tracker initialized
- Sprint 3 merged to main with QA sign-off and handoff artifacts

## 8. Current State (rewritten every sprint)

Repository state:
- Sprint 1 is merged to main and documented as completed.
- Sprint 2 is merged to main with complete handoff artifacts.
- Sprint 3 is merged to main with complete handoff artifacts.
- Sprint 4 branch is active with planning artifacts initialized.

Technical baseline:
- PostgreSQL schema migrations exist through 0007.
- Security and environment strategy documented (ADR-003, ADR-004).
- Health/readiness and baseline structured logging are active.
- RBAC enforced across critical routes with explicit endpoint policy.
- Current service date uses PostgreSQL timezone-aware clock for day-based flows.
- Automated regression suite and sprint QA checks are passing.
- Confirm flow hardened against invalid actor UUID input.
- Next implementation target is auth source hardening and first cash/output module skeleton routes.
- Auth mode abstraction is implemented with strict header validation mode.
- Cash window and outputs now have first executable service/repository/route skeletons.
- Regression suite currently passes with Sprint 3 increments.
- Next target is full workflow transitions for cash sessions and outputs approvals.

Immediate next move:
- Implement cash session line update/recalculate/close/reopen transitions.
- Implement outputs submit/approve/paid transitions with event logging.
- Add transition tests and complete Sprint 4 QA playthrough.

## 9. Security Rules

Mandatory rules:
- Never hardcode credentials in source code.
- Use .env only for local; secure secret injection in non-local environments.
- Validate upload mime type and max size.
- Sanitize file names and block path traversal.
- Enforce RBAC for treasurer/admin/auditor.
- Preserve immutable audit history for sensitive edits and approvals.
- Restrict admin routes with stronger auth controls.

Operational controls:
- Health endpoint: /healthz
- Readiness endpoint: /readyz
- Structured logs with request identifiers
- Backup and restore verification cadence at least weekly

## 10. How to Run Locally

Prerequisites:
- Python 3.11+
- PostgreSQL 15+
- Optional: Docker Desktop

Option A: native Python
1. Create env: python -m venv .venv
2. Activate env: source .venv/bin/activate
3. Install deps: pip install -r requirements.txt
4. Copy env file: cp .env.example .env
5. Set DATABASE_URL and strategy env vars
6. Apply migrations in order from db/migrations
7. Run app entrypoint (main.py when scaffold is committed)

Option B: Docker Compose (recommended)
1. docker compose up --build
2. Confirm app and DB services healthy
3. Run smoke flow: upload envelope -> review -> confirm -> summary

Build checklist for first executable increment:
- App scaffold with interfaces/strategies/repositories/services/ui
- Migration runner and DB connectivity
- Core endpoints for capture/review/confirm/summary
- Basic day-log deferred correction with field audit writing

## 11. How to Deploy

Phase 1 deployment profile:
- Linux Docker host
- Flask behind Gunicorn
- cloudflared sidecar/service for ingress via Cloudflare
- PostgreSQL managed on trusted host/network

Deployment steps:
1. Build versioned container image
2. Inject non-local secrets from secret store
3. Run DB migrations before app rollout
4. Start app + scheduler as separate processes
5. Verify /healthz and /readyz
6. Run smoke tests for capture and cash close
7. Keep rollback image and migration rollback plan ready

## 12. Cross-Chat Handoff Protocol

Context persistence contract:
- Producer updates PROJECT_BRIEF sections 7 and 8 at sprint boundaries.
- Dev team updates docs/sprint-N/progress.md after each phase.
- End of sprint always writes docs/sprint-N/done.md.

Cold start protocol for any new chat:
1. Read PROJECT_BRIEF.md.
2. Read docs/sprint-N/progress.md for active sprint.
3. Resume only unfinished tasks listed in progress.md.

Handoff message template:
- Completed:
- In progress:
- Blockers:
- Next command to run:
- Files changed:
- Open issues:

## 13. Bug & Fix Tracking

Single source of truth for defects: GitHub Issues.

Rules:
- Every bug found in QA playthrough must become an issue.
- Every bug-fix commit references issue id, for example: Fixes #NN.
- Avoid batch fix-everything commits; keep one logical fix per commit.
- docs/sprint-N/progress.md must list issue ids and status changes.

Bug lifecycle:
- QA files issue -> Dev reproduces -> Dev fixes with tests -> QA verifies -> close issue

## 14. Multi-Repo Setup

Separate clones per team workspace:
- project-dev: implementation branch work
- project-qa: verification and sign-off
- project-devops: deployment and runtime scripts (as needed)

Branch strategy:
- main is protected.
- One feature branch per sprint or feature stream, e.g. feature/sprint-1.
- Merge commits preferred; avoid rebase-based history rewriting.
- Producer coordinates merge order after QA pass.

Merge rules:
- No direct push to main.
- Required: tests green + QA sign-off artifact for sprint scope.
- Update sprint docs before merge completion.
