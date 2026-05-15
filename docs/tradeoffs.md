# Tradeoffs

Placeholder. Record intentional decisions, rejected alternatives, and constraints (cost, complexity, vendor lock-in, operability).

## Decision log

| Date | Decision | Rationale | Alternatives considered |
|------|----------|-----------|---------------------------|
| 2026-05-15 | Local dev via Docker Compose; bind mounts for `./ansible/` and `./logs/`, named volume for Postgres | Low ceremony for a two-service stack; host-visible generated assets; DB data managed by Docker | Kubernetes / Kind for local parity; bind-mounting Postgres data into the repo |

## Open questions

_TBD_
