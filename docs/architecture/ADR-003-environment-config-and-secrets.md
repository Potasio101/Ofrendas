# ADR-003: Environment Configuration and Secret Management

- Status: Accepted
- Date: 2026-05-08

## Context

The application uses configurable repositories and strategies across environments. In the current phase, PostgreSQL is the operational datastore and optional external integrations are deferred.

## Decision Drivers

- Prevent hardcoded credentials.
- Keep deployment environment-specific and auditable.
- Allow strategy switching through configuration.

## Options Considered

1. Hardcoded config values in Python modules.
2. `.env` files for all environments.
3. `.env` for local only and secret manager for non-local.

## Decision

Choose option 3.

- Local: use `.env` derived from `.env.example`.
- Staging/production: inject secrets from secure secret store.
- Switch strategies and repositories through environment variables.

## Rationale

This enables local productivity while meeting baseline production security expectations.

## Consequences

- Positive:
  - Reduced secret leakage risk.
  - Consistent configuration model.
  - Easier audit and rotation.
- Negative:
  - Requires deployment pipeline support for secret injection.

## Implementation Notes

- Required variable: `APP_ENV`.
- Recommended variables: `OCR_STRATEGY`, `CORRECTION_STRATEGY`, `STORAGE_BACKEND`, `DATABASE_URL`.
- Never commit real credentials or production `.env` files.