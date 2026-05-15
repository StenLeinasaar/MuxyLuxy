# Testing

We keep a **thin, explicit smoke layer** for the Compose stack: fast feedback that services are up and reachable the same way a developer (or CI runner on the host) would hit them.

## What we run today

| Script | Purpose |
|--------|---------|
| `scripts/wait-for-api.sh` | Polls `GET http://localhost:8000/healthz` (up to ~30s). |
| `scripts/wait-for-targets.sh` | Polls TCP **127.0.0.1:2221** and **:2222** until both accept a connection (up to ~30s). |
| `scripts/smoke-test.sh` | **One-shot:** health endpoint contains `ok`, then verifies both SSH ports respond. |
| `scripts/test.sh` | Delegates to `smoke-test.sh` so `./scripts/test.sh` stays the single “full smoke” entrypoint. |

## Makefile shortcuts

| Target | Runs |
|--------|------|
| `make wait-api` | `./scripts/wait-for-api.sh` |
| `make wait-targets` | `./scripts/wait-for-targets.sh` |
| `make wait` | `wait-api` then `wait-targets` |
| `make smoke` | `./scripts/smoke-test.sh` |

**Suggested order after `make up` (or `docker compose up -d --build`):** `make wait` then `make smoke`. Waits avoid racing a still-starting container; smoke asserts the stack is actually usable.

## Design choices

**Host-side checks (curl + localhost ports)**  
Smoke runs from the **repository host**, not `docker compose exec`. That validates **published ports** and the same path a human uses (`curl` / SSH client). It does not prove in-container-only bugs, but it matches how we develop and how lightweight CI often drives Compose.

**`python3` for target readiness**  
TCP checks use `socket.create_connection` in small embedded scripts instead of `nc` or bash `/dev/tcp`. **Reason:** consistent behavior on macOS and Linux without assuming optional CLI tools.

**Smoke vs “real” tests**  
There is **no** unit or integration test suite in-repo yet. When we add one, keep **smoke** as the outer gate (Compose up → wait → smoke); keep fast tests (lint/unit) separate so they can run without Docker when possible.
