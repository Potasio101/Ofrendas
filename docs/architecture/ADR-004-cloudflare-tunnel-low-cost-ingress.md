# ADR-004: Secure Ingress with Cloudflare Tunnel for Low-Cost Hosting

- Status: Accepted
- Date: 2026-05-08

## Context

The project targets low traffic (30-40 envelopes per week), a near-zero budget, and a team experienced in Linux, Docker, cloud tooling, and M365. The service may run on a local or self-managed Docker host.

## Decision Drivers

- Avoid public exposure of host ports.
- Keep recurring cost minimal.
- Reduce operational complexity for a small team.
- Maintain secure remote access for treasurer workflows.

## Options Considered

1. Public IP + Nginx + certificate management on host.
2. Cloudflare Tunnel from Docker host to Cloudflare edge.
3. Managed cloud load balancer + container platform.

## Decision

Choose option 2.

- Run `cloudflared` as a Docker service on the host.
- Route public traffic through Cloudflare edge to internal Flask/Gunicorn service.
- Enforce access policies for admin routes with Cloudflare Access.

## Rationale

This provides encrypted edge connectivity and basic protection without exposing inbound ports, while staying aligned with cost constraints.

## Consequences

- Positive:
  - No open inbound ports required.
  - Low-cost ingress path for initial phase.
  - Fast setup with existing team skills.
- Negative:
  - Dependency on Cloudflare availability.
  - Additional tunnel service to monitor.

## Implementation Notes

- Keep local-only fallback operation if tunnel is unavailable.
- Add health checks for both app and `cloudflared` container.
- Restrict upload endpoint size and request rate at edge.