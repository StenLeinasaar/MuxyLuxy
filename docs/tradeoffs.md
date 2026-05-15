# Tradeoffs

Placeholder. Record intentional decisions, rejected alternatives, and constraints (cost, complexity, vendor lock-in, operability).

## Decision log

| Date | Decision | Rationale | Alternatives considered |
|------|----------|-----------|---------------------------|
| 2026-05-15 | Local dev via Docker Compose; bind mounts for `./ansible/` and `./logs/`, named volume for Postgres | Low ceremony for a two-service stack; host-visible generated assets; DB data managed by Docker | Kubernetes / Kind for local parity; bind-mounting Postgres data into the repo |
| 2026-05-15 | Two Compose services `target1` / `target2`, same image, distinct host ports **2221** / **2222** | Mirrors multiple hosts without port clashes; one Dockerfile to maintain | Single target; dynamic Compose scale (harder to pin fixed smoke ports) |
| 2026-05-15 | Target image: Debian slim + `openssh-server`, `python3`, `sudo`; user `ansible` with NOPASSWD sudo | Matches common Ansible targets; supports `become` checks without extra layers | Alpine (musl differences); cloud VM-only testing (slower, not offline) |
| 2026-05-15 | Smoke: `curl` API + `python3` TCP to SSH ports; separate **wait** scripts | Waits handle slow startup; smoke stays a strict assertion; Python avoids `nc` / bash TCP portability gaps | Poll `docker compose ps` only (skips published-port wiring); embed long retries only inside smoke |

## Open questions

_TBD_
