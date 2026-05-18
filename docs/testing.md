# Testing

We keep a **thin, explicit smoke layer** for the Compose stack: fast feedback that services are up and reachable the same way a developer (or CI runner on the host) would hit them.

## What we run today

| Script | Purpose |
|--------|---------|
| `scripts/wait-for-api.sh` | Polls `GET http://localhost:8000/healthz` (up to ~30s). |
| `scripts/wait-for-targets.sh` | Polls TCP **127.0.0.1:2221** and **:2222** until both accept a connection (up to ~30s). |
| `scripts/smoke-test.sh` | **One-shot:** health endpoint contains `ok`, then auth/CRUD-style API checks and both SSH ports respond. |
| `scripts/test.sh` | Runs **`pytest`** inside the `api` container (`docker compose exec -T api pytest`). |

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

**Smoke vs service tests**  
`make test` runs **`pytest`** inside the `api` container (`scripts/test.sh`), including **`GET /metrics`** checks in `service/tests/test_metrics.py` against the same FastAPI app as production (`app.main`). Metrics scraping in Compose is covered by the **Prometheus** service (see `docs/architecture.md`). Keep **smoke** as the outer gate for a live stack (Compose up → wait → smoke); keep **pytest** for fast in-container API checks.
