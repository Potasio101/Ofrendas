# ADR-001: Runtime and Deployment Topology

- Status: Accepted
- Date: 2026-05-08

## Context

The system must run quickly in local development and evolve safely into production. The architecture uses Flask, strategy-based OCR/correction, and PostgreSQL as the operational source-of-truth.

## Decision Drivers

- Keep developer setup simple.
- Enable reliable production operation.
- Support low initial scale and future growth.
- Minimize architecture rewrites between environments.

## Options Considered

1. Flask built-in server in all environments.
2. Flask built-in server locally, Gunicorn + Nginx in production.
3. Full Kubernetes stack from day one.

## Decision

Choose option 2.

- Local: Flask app with debug mode and local backends.
- Production: Nginx (TLS, limits) in front of Gunicorn (multiple workers).
- Scheduler/training job runs as a separate process.

## Rationale

This choice balances simplicity and reliability. It avoids over-engineering for current scale while enabling production hardening.

## Consequences

- Positive:
  - Fast local iteration.
  - Better production resilience and security controls.
  - Clear upgrade path to containers or orchestration later.
- Negative:
  - Need to maintain process management for web and scheduler.
  - Additional Nginx/Gunicorn operational setup.

## Implementation Notes

- Add `/healthz` and `/readyz` endpoints.
- Use environment variable `APP_ENV` to switch wiring.
- Keep `debug=false` outside local environment.