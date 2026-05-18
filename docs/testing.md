# Testing

We use **three automated layers** plus **manual** checks: fast **pytest** in the API container, **host-side smoke** against published ports, and an **E2E** script that runs real Ansible against the Compose SSH targets.

## Unit tests

- **Location:** `service/tests/`.
- **Style:** `pytest` with per-module **fixtures** that build a **`TestClient`** against **`app.main:app`** and use **`SessionLocal`** (same SQLAlchemy stack as production).
- **Scope:** Focused tests for auth, validation edge cases, metrics wiring, and small helpers where splitting them out keeps failures obvious.

**Command:** `make test` runs `docker compose exec -T api pytest` (`scripts/test.sh`). Requires the **`api`** service to be running (tests use the container’s **`DATABASE_URL`**, typically **Postgres** from Compose).

## API tests

- **Same runner as unit tests:** `pytest` + **`TestClient`**.
- **Scope:** Endpoints under **`/login`**, **`/me`**, **`/targets`**, **`/roles`**, **`/run`**, **`/status`**, **`/logs`**, **`/healthz`**, and **`/metrics`** — request/response contracts, status codes, and auth behavior against the **real database** configured for the `api` service (tests often **delete** rows they create).

**Command:** `make test` (includes these).

## Smoke tests

- **Script:** `scripts/smoke-test.sh`.
- **Environment:** Runs on the **host**, default **`ROLLER_API_URL=http://localhost:8000`**.
- **What it covers:** `GET /healthz` (status + database), **`401`** on unauthenticated **`GET /targets`**, **`POST /login`**, **`GET /me`**, CRUD-style **`PUT`/`GET`/`DELETE`** for a temporary target and role (role path defaults to **`/opt/ansible/roles/base`** inside the API container), **`GET /status`**, and **TCP connect** to **127.0.0.1:2221** and **2222** (SSH targets).
- **Dependencies:** `curl`, `jq`, `python3`.

**Commands:**

```bash
make wait-api          # optional but avoids races right after compose up
make smoke
```

`make wait` runs **`wait-api`** then **`wait-targets`** (`scripts/wait-for-targets.sh`).

## End-to-end tests

- **Script:** `scripts/e2e-run-role.sh`.
- **Prerequisites:** Compose stack up; **`scripts/bootstrap.sh`** has created **`./ssh/id_rsa`**; **`api`**, **`target1`**, **`target2`** healthy enough to accept SSH and HTTP.
- **Flow:** Restarts `api` and targets if needed so key mounts are consistent → waits for API and SSH ports → logs in → **`scripts/seed-demo-data.sh`** registers **`target1`/`target2`** and roles **`base`**, **`motd`**, **`packages`** → queues **three** **`POST /run`** calls for **`motd`** → polls **`GET /status`** until all succeed or any fail (prints **`GET /logs`** for failures).

**Commands:**

```bash
make e2e               # default paths suit the dockerized API
make e2e-local         # API on host: sets ROLLER_ROLES_ROOT and ROLLER_SSH_KEY_PATH
```

## Manual verification

| Check | How |
|-------|-----|
| **OpenAPI** | Visit `http://localhost:8000/docs` after `docker compose up`. |
| **Database** | `docker compose exec postgres psql -U roller -d roller -c '\dt'` (adjust user/db from `.env`). |
| **Ansible output** | Inspect `ansible/generated/<run_id>/` and `logs/<run_id>.log` on the host after a run. |
| **SSH into targets** | `ssh -p 2221 ansible@127.0.0.1` (lab image password; keys may also apply depending on image setup). |
| **Prometheus targets** | `http://localhost:9090` → **Status → Targets** → `ansible-roller-api` **UP**. |
| **Ansible ping** | `make check-ansible` / `make check-ssh` (see `scripts/`). |

## Design choices

**Host-side smoke (curl + localhost ports)**  
Validates **published ports** the way humans and CI do. It does not catch bugs visible only inside the container network without host publishing.

**`python3` for target readiness**  
TCP checks use `socket.create_connection` instead of `nc` or bash `/dev/tcp` for consistent macOS/Linux behavior.

**Smoke vs pytest**  
Smoke is the **outer gate** for a live Compose stack; **`make test`** is the **fast feedback** loop for API semantics without rebuilding the whole lab.

---

## Full example flow

From the repository root (see **README** for notes on foreground vs detached `up`):

```bash
cp .env.example .env
make up
make wait-api
make smoke
make e2e
```

If `make up` is holding the terminal, run **`make wait-api`** / **`make smoke`** / **`make e2e`** in a **second** terminal, or start the stack with **`docker compose up -d --build`** after `./scripts/bootstrap.sh`.

**One-shot local gate:** `make verify` runs **`lint`**, **`test`**, **`smoke`**, and **`e2e`**.
