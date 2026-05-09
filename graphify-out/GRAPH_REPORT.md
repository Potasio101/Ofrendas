# Graph Report - .  (2026-05-09)

## Corpus Check
- Corpus is ~32,809 words - fits in a single context window. You may not need a graph.

## Summary
- 803 nodes · 915 edges · 77 communities (66 shown, 11 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 53 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]

## God Nodes (most connected - your core abstractions)
1. `PostgreSQLRepo` - 41 edges
2. `_build_client()` - 27 edges
3. `OfferingService` - 24 edges
4. `App de Ofrendas — LLM Prompt Plan v1.0` - 20 edges
5. `PROJECT_BRIEF` - 15 edges
6. `_build_client()` - 14 edges
7. `Flow Specification - Ofrendas Core (Figma Ready)` - 13 edges
8. `_normalize_uuid()` - 12 edges
9. `build_app()` - 11 edges
10. `create_app()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `build_app()` --calls--> `AppConfig`  [INFERRED]
  main.py → offering_app/config.py
- `build_app()` --calls--> `ensure_data_dirs()`  [INFERRED]
  main.py → offering_app/config.py
- `build_app()` --calls--> `FuzzyCorrection`  [INFERRED]
  main.py → offering_app/strategies/fuzzy_correction.py
- `build_app()` --calls--> `PostgreSQLRepo`  [INFERRED]
  main.py → offering_app/repositories/postgresql_repo.py
- `build_app()` --calls--> `OfferingService`  [INFERRED]
  main.py → offering_app/services/offering_service.py

## Communities (77 total, 11 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.0
Nodes (27): _build_client(), DummyCashWindowService, DummyKioskPOSService, DummyOutputsService, DummyService, DummyStorage, DummySummary, test_cash_window_close_allows_treasurer() (+19 more)

### Community 1 - "Community 1"
Cohesion: 0.0
Nodes (21): ABC, ICorrectionStrategy, IOCRStrategy, IStorageRepo, ITrainingRepo, Correction, Offering, _normalize_uuid() (+13 more)

### Community 2 - "Community 2"
Cohesion: 0.0
Nodes (10): _build_client(), DummyCashWindowService, DummyKioskPOSService, DummyOutputsService, DummyService, DummyStorage, DummySummary, test_workflow_cash_view_renders_for_auditor() (+2 more)

### Community 3 - "Community 3"
Cohesion: 0.0
Nodes (3): IStorageRepo, _normalize_uuid(), PostgreSQLRepo

### Community 4 - "Community 4"
Cohesion: 0.0
Nodes (5): CashWindowService, KioskPOSService, OutputsService, _configure_logging(), create_app()

### Community 5 - "Community 5"
Cohesion: 0.0
Nodes (15): _build_client(), DummyService, DummyStorage, DummySummary, _signed_headers(), test_header_strict_allows_with_valid_identity_headers(), test_header_strict_denies_invalid_role_header(), test_header_strict_denies_missing_identity_headers() (+7 more)

### Community 6 - "Community 6"
Cohesion: 0.0
Nodes (9): IOCRStrategy, ITrainingRepo, AppConfig, ensure_data_dirs(), build_app(), load_members(), TrainingRepo, ImageProcessor (+1 more)

### Community 7 - "Community 7"
Cohesion: 0.0
Nodes (10): _build_client(), DummyService, DummyStorage, DummySummary, test_admin_config_allowed_for_admin_role(), test_admin_config_forbidden_for_treasurer_role(), test_confirm_allowed_for_treasurer_role(), test_confirm_forbidden_for_auditor_role() (+2 more)

### Community 8 - "Community 8"
Cohesion: 0.0
Nodes (20): Constraints, Current Pain Points, Current Pain Points, Current Pain Points, Current Pain Points, Current Pain Points, Desired Outcomes, Desired Outcomes (+12 more)

### Community 9 - "Community 9"
Cohesion: 0.0
Nodes (6): _build_client(), DummyService, DummyStorage, DummySummary, test_day_log_uses_storage_current_service_date_by_timezone(), test_summary_uses_storage_current_service_date_by_timezone()

### Community 10 - "Community 10"
Cohesion: 0.0
Nodes (18): ADRs, Alcance actual, App + PostgreSQL con Docker, Base de datos, code:bash (docker compose up -d postgres), code:bash (for f in db/migrations/000[1-7]*.sql; do), code:env (DATABASE_URL=postgresql://ofrendas:ofrendas@localhost:5432/o), code:bash (docker compose up -d --build app) (+10 more)

### Community 11 - "Community 11"
Cohesion: 0.0
Nodes (16): 10. How to Run Locally, 11. How to Deploy, 12. Cross-Chat Handoff Protocol, 13. Bug & Fix Tracking, 14. Multi-Repo Setup, 1. Project Overview, 2. Concept / Product Description, 3. Tech Stack (+8 more)

### Community 12 - "Community 12"
Cohesion: 0.0
Nodes (17): code:block10 (Crea services/image_processor.py siguiendo Single Responsibi), code:block11 (Crea los repositorios implementando IStorageRepo e ITraining), code:block12 (Crea services/offering_service.py — el orquestador central.), code:block13 (Crea ui/app.py con Flask y el HTML completo de la app del te), code:block14 (Crea services/training_job.py — el job nocturno que corre a ), code:block15 (Crea main.py — el punto de entrada que conecta todo usando), code:block8 (Eres un arquitecto de software senior. Crea las interfaces y), code:block9 (Usando las interfaces del paso anterior, crea las implementa) (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.0
Nodes (16): Accessibility Requirements, Entry Points, Figma Handoff Notes, Flow Specification - Ofrendas Core (Figma Ready), Global Design Principles, Key Components For Figma Library, Keyboard Navigation, Screen Flow 1 - Envelope Capture (+8 more)

### Community 14 - "Community 14"
Cohesion: 0.0
Nodes (14): ADRs Asociados, App de Ofrendas — LLM Prompt Plan v1.0, Arquitectura, Checklist de Preparacion para Produccion, code:python (# main.py — Cambiar de EasyOCR a Tesseract en UNA línea:), code:block6 (📱 UI Flask), code:block7 (offering_app/), Estructura de Carpetas (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.0
Nodes (6): ICorrectionStrategy, FuzzyCorrection, # TODO: Load and use the trained model in phase 2., TrainedCorrection, test_amount_field_is_normalized_to_numeric_text(), test_member_name_is_matched_to_closest_known_member()

### Community 16 - "Community 16"
Cohesion: 0.0
Nodes (11): code:block1 (ImageProcessor  → solo limpia imagen), code:block2 (TitheStrategy, OfferingStrategy, TalentoStrategy, OfrendaDeA), code:block3 (OCRStrategy → EasyOCRStrategy), code:block4 (IReader     → solo read()), code:block5 (OfferingService(repo: IStorage)), D — Dependency Inversion, I — Interface Segregation, L — Liskov Substitution (+3 more)

### Community 17 - "Community 17"
Cohesion: 0.0
Nodes (10): Alternativa local recomendada con Docker, code:env (APP_ENV=local), code:bash (python -m venv .venv), code:bash (docker compose up --build), Comandos recomendados, Objetivo, Perfil de ejecucion local, Runbook de Desarrollo Local (+2 more)

### Community 18 - "Community 18"
Cohesion: 0.0
Nodes (10): Cadencia operativa recomendada, Capacidad objetivo para esta fase, code:text (Usuario movil), Confiabilidad y fallback, Controles de seguridad minimos, Objetivo, Observabilidad minima, Perfil de ejecucion produccion (+2 more)

### Community 19 - "Community 19"
Cohesion: 0.0
Nodes (9): Definition of Done global, Developer Task List - Ofrendas, Orden recomendado de ejecucion, Task 1 - Extraer logica de OCR fallback fuera de UI, Task 2 - Eliminar SQL directo desde main, Task 3 - Harden de auth por entorno, Task 4 - Docker runtime para produccion, Task 5 - Dividir UI monolitica en modulos (+1 more)

### Community 20 - "Community 20"
Cohesion: 0.0
Nodes (9): Persona, Stage 1 - Start Of Day, Stage 2 - Envelope Intake Rush, Stage 3 - Deferred Correction, Stage 4 - Cash Reconciliation, Stage 5 - Outputs And Approvals, Stage 6 - Kiosk Sales (If Active), Stage 7 - End Of Day Audit Readiness (+1 more)

### Community 21 - "Community 21"
Cohesion: 0.0
Nodes (9): code:text (IExportStrategy), code:python (class IExportStrategy(ABC):), Contrato sugerido para export, Estrategia de Exportaciones Contables, Flujo recomendado, Formatos de salida iniciales, Modo smart: upload de esquema CSV + mapping dinamico, Objetivo (+1 more)

### Community 22 - "Community 22"
Cohesion: 0.0
Nodes (8): ADR-001: Runtime and Deployment Topology, Consequences, Context, Decision, Decision Drivers, Implementation Notes, Options Considered, Rationale

### Community 23 - "Community 23"
Cohesion: 0.0
Nodes (8): ADR-005: Multi-Provider Accounting Export Architecture, Consequences, Context, Decision, Decision Drivers, Implementation Notes, Options Considered, Rationale

### Community 24 - "Community 24"
Cohesion: 0.0
Nodes (8): ADR-011: Outputs Control with Fund Source and Approval Audit, Consequences, Context, Decision, Decision Drivers, Implementation Notes, Options Considered, Rationale

### Community 25 - "Community 25"
Cohesion: 0.0
Nodes (8): ADR-006: PostgreSQL as Single Source of Truth for App Operations and Reporting, Consequences, Context, Decision, Decision Drivers, Implementation Notes, Options Considered, Rationale

### Community 26 - "Community 26"
Cohesion: 0.0
Nodes (8): ADR-009: Cash Window with Daily Close and Audit Trail, Consequences, Context, Decision, Decision Drivers, Implementation Notes, Options Considered, Rationale

### Community 27 - "Community 27"
Cohesion: 0.0
Nodes (8): ADR-004: Secure Ingress with Cloudflare Tunnel for Low-Cost Hosting, Consequences, Context, Decision, Decision Drivers, Implementation Notes, Options Considered, Rationale

### Community 28 - "Community 28"
Cohesion: 0.0
Nodes (8): ADR-002: PostgreSQL as Primary Operational Storage (SharePoint Deferred), Consequences, Context, Decision, Decision Drivers, Implementation Notes, Options Considered, Rationale

### Community 29 - "Community 29"
Cohesion: 0.0
Nodes (8): ADR-008: Deferred Correction Workflow and Field-Level Audit in UI, Consequences, Context, Decision, Decision Drivers, Implementation Notes, Options Considered, Rationale

### Community 30 - "Community 30"
Cohesion: 0.0
Nodes (8): ADR-010: Kiosk POS Mode with Cash/Zelle and Custom Items, Consequences, Context, Decision, Decision Drivers, Implementation Notes, Options Considered, Rationale

### Community 31 - "Community 31"
Cohesion: 0.0
Nodes (8): ADR-007: Schema-Driven CSV Mapping for Accounting Exports, Consequences, Context, Decision, Decision Drivers, Implementation Notes, Options Considered, Rationale

### Community 32 - "Community 32"
Cohesion: 0.0
Nodes (7): Handoff Commands, Issues Found and Resolved, Next Sprint Inputs, Remaining Risks, Sprint 6 Done Handoff, Validation Summary, What Was Delivered

### Community 33 - "Community 33"
Cohesion: 0.0
Nodes (7): Handoff Commands, Issues Found and Resolved, Next Sprint Inputs, Remaining Risks, Sprint 1 Done Handoff, Validation Summary, What Was Delivered

### Community 34 - "Community 34"
Cohesion: 0.0
Nodes (7): Acceptance Criteria, Definition of Done, In Scope, Out of Scope, Sprint 1 Plan - Foundation and First Vertical Slice, Sprint Goal, Work Breakdown

### Community 35 - "Community 35"
Cohesion: 0.0
Nodes (7): Handoff Commands, Issues Found and Resolved, Next Sprint Inputs, Remaining Risks, Sprint 4 Done Handoff, Validation Summary, What Was Delivered

### Community 36 - "Community 36"
Cohesion: 0.0
Nodes (7): Acceptance Criteria, Definition of Done, In Scope, Out of Scope, Sprint 4 Plan - Cash Window Full Flow and Outputs Approval Workflow, Sprint Goal, Work Breakdown

### Community 37 - "Community 37"
Cohesion: 0.0
Nodes (7): Handoff Commands, Issues Found and Resolved, Next Sprint Inputs, Remaining Risks, Sprint 3 Done Handoff, Validation Summary, What Was Delivered

### Community 38 - "Community 38"
Cohesion: 0.0
Nodes (7): Acceptance Criteria, Definition of Done, In Scope, Out of Scope, Sprint 3 Plan - Authentication Hardening and Module Expansion Start, Sprint Goal, Work Breakdown

### Community 39 - "Community 39"
Cohesion: 0.0
Nodes (7): Handoff Commands, Issues Found and Resolved, Next Sprint Inputs, Remaining Risks, Sprint 2 Done Handoff, Validation Summary, What Was Delivered

### Community 40 - "Community 40"
Cohesion: 0.0
Nodes (7): Acceptance Criteria, Definition of Done, In Scope, Out of Scope, Sprint 2 Plan - Auth/RBAC Hardening and Timezone Normalization, Sprint Goal, Work Breakdown

### Community 41 - "Community 41"
Cohesion: 0.0
Nodes (7): Handoff Commands, Issues Found and Resolved, Next Sprint Inputs, Remaining Risks, Sprint 5 Done Handoff, Validation Summary, What Was Delivered

### Community 42 - "Community 42"
Cohesion: 0.0
Nodes (7): Acceptance Criteria, Definition of Done, In Scope, Out of Scope, Sprint 5 Plan - Identity Provider Integration and Workflow UX Hardening, Sprint Goal, Work Breakdown

### Community 43 - "Community 43"
Cohesion: 0.0
Nodes (7): code:bash (export DATABASE_URL="postgresql://ofrendas:ofrendas@localhos), code:bash (docker exec -i postgres psql -U ofrendas -d ofrendas -v ON_E), Files, Notes, PostgreSQL migrations, Run against Docker postgres, Run with psql

### Community 44 - "Community 44"
Cohesion: 0.0
Nodes (6): Acceptance Criteria, Definition of Done, In Scope, Out of Scope, Sprint 6 Plan - Proxy Signed Identity and Workflow UI Foundations, Sprint Goal

### Community 45 - "Community 45"
Cohesion: 0.0
Nodes (6): Agent Positions, Brainstorm 001 - Ofrendas Build Kickoff, Decisions, Prompt Used, Real Disagreements, Risks and Mitigations

### Community 46 - "Community 46"
Cohesion: 0.0
Nodes (6): Evidence Summary, Notes, Open Issues, QA Sign-off - Sprint 5, Recommendation, Scope Validated

### Community 47 - "Community 47"
Cohesion: 0.0
Nodes (6): Evidence Summary, Notes, Open Issues, QA Sign-off - Sprint 2, Recommendation, Scope Validated

### Community 48 - "Community 48"
Cohesion: 0.0
Nodes (6): Evidence Summary, Notes, Open Issues, QA Sign-off - Sprint 1, Recommendation, Scope Validated

### Community 49 - "Community 49"
Cohesion: 0.0
Nodes (6): Evidence Summary, Notes, Open Issues, QA Sign-off - Sprint 4, Recommendation, Scope Validated

### Community 50 - "Community 50"
Cohesion: 0.0
Nodes (6): Evidence Summary, Notes, Open Issues, QA Sign-off - Sprint 3, Recommendation, Scope Validated

### Community 51 - "Community 51"
Cohesion: 0.0
Nodes (6): Evidence Summary, Notes, Open Issues, QA Sign-off - Sprint 6, Recommendation, Scope Validated

### Community 52 - "Community 52"
Cohesion: 0.0
Nodes (6): Campos minimos por ticket, Flujo base, Items custom, Kiosk Mode (POS) - Tiendita, Objetivo, Reglas de negocio

### Community 53 - "Community 53"
Cohesion: 0.0
Nodes (6): Campos minimos por salida, Casos comunes, Control de Salidas (Outputs), Objetivo, Politica de fondos (flexible), Reglas de negocio

### Community 54 - "Community 54"
Cohesion: 0.0
Nodes (5): Checklist, Open Blockers, Phase Notes, Related Issues, Sprint 6 Progress Tracker

### Community 55 - "Community 55"
Cohesion: 0.0
Nodes (5): Checklist, Open Blockers, Phase Notes, Related Issues, Sprint 1 Progress Tracker

### Community 56 - "Community 56"
Cohesion: 0.0
Nodes (5): Checklist, Open Blockers, Phase Notes, Related Issues, Sprint 4 Progress Tracker

### Community 57 - "Community 57"
Cohesion: 0.0
Nodes (5): Checklist, Open Blockers, Phase Notes, Related Issues, Sprint 3 Progress Tracker

### Community 58 - "Community 58"
Cohesion: 0.0
Nodes (5): Checklist, Open Blockers, Phase Notes, Related Issues, Sprint 2 Progress Tracker

### Community 59 - "Community 59"
Cohesion: 0.0
Nodes (5): Checklist, Open Blockers, Phase Notes, Related Issues, Sprint 5 Progress Tracker

### Community 60 - "Community 60"
Cohesion: 0.0
Nodes (5): Decision, Matriz de source-of-truth (alineada con ADR-002 y ADR-006), Modelo de Datos (PostgreSQL + Export Opcional), Riesgos y mitigaciones, Ventajas

### Community 62 - "Community 62"
Cohesion: 0.0
Nodes (4): Decision de Contexto Confirmado (Mayo 2026), Hallazgos Criticos, Review de Arquitectura (Local Ahora, Produccion Futuro), Supuestos de Escala (para decisiones actuales)

## Knowledge Gaps
- **348 isolated node(s):** `Ofrendas application package.`, `Strategy implementations.`, `# TODO: Load and use the trained model in phase 2.`, `Persistence adapters.`, `Application services.` (+343 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.