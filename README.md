# MuxyLuxy

Infrastructure automation engineering.

## What exists today (phase 1)

- **FastAPI service** (`service/`) — minimal app with `GET /healthz`, packaged with `pyproject.toml` (Python 3.12) and a **Dockerfile** that runs Uvicorn on port 8000.
- **Local stack** — `docker-compose.yml` runs **Postgres 16** (with a named volume and healthcheck), the **api** service, and two **SSH targets** (`target1`, `target2`) built from `targets/` for Ansible-style iteration; the API waits until Postgres is healthy before starting.
- **Environment** — `.env.example` documents variables; copy to `.env` for overrides. Database URL targets the `postgres` service on the Compose network.
- **Ansible-related paths** — Stored as **paths relative to the API working directory** (`/app` in the container). Compose **bind-mounts** the repo’s `./ansible/` to `/app/ansible` and `./logs/` to `/app/logs`, so when you run Compose from the **repository root**, those directories align with the paths on your machine (see `docs/local-development.md`).
- **Scripts** — `scripts/test.sh` (runs full smoke), `scripts/lint.sh` (placeholder), `scripts/smoke-test.sh`, `scripts/wait-for-api.sh`, `scripts/wait-for-targets.sh`.
- **Docs** — `docs/architecture.md` (stack and `targets/`), `docs/testing.md` (smoke and wait scripts), `docs/tradeoffs.md` (decision log), `docs/security.md` (local SSH target caveats). **Local dev rationale:** `docs/local-development.md` (Compose vs Kind, bind mounts vs named volumes).

### Quick start

```bash
cp .env.example .env   # optional; compose has defaults
docker compose up --build
```

Smoke check (from repo root, after stack is up): `make wait` then `make smoke` (or `./scripts/smoke-test.sh`). See `docs/testing.md`.

## Repository layout

| Path | Purpose |
|------|---------|
| `docs/` | Documentation |
| `scripts/` | Shell and helper scripts |
| `service/` | Application or service code |
| `ansible/` | Ansible playbooks, roles, inventory (layout TBD); bind-mounted into the API container |
| `targets/` | Dockerfile and config for local **SSH target** images (`target1`, `target2`) |
| `examples/` | Example configurations and snippets |
| `logs/` | Service log output directory; bind-mounted for the API |

## Decisions so far

| Topic | Choice | Rationale |
|-------|--------|-----------|
| API framework | FastAPI | Async-friendly HTTP API; simple health endpoint for compose/smoke tests |
| Python packaging | `pyproject.toml` + setuptools | Standard install in Docker via `pip install .` |
| Database | Postgres 16 (Alpine) in Compose | Matches SQLAlchemy/psycopg stack declared for later phases |
| API startup order | `depends_on` + Postgres `healthcheck` | Avoids connection races against a not-yet-ready database |
| Ansible paths | Relative paths + bind mounts | Keeps artifacts under the repo root (`ansible/`, `logs/`) instead of hard-coded absolute paths; local dev matches “run from project root” |
| SSH lab targets | `target1` / `target2`, host ports **2221** / **2222** | Two hosts with fixed smoke ports; one image under `targets/` (vs one host or random published ports, harder to script) |
| Smoke testing | Host `curl` + `python3` TCP; `make wait` then `make smoke` | Validates published ports the way developers hit them; no `nc` dependency (vs in-container-only checks that skip port publishing) |
| Generated output & logs | Gitignored (`ansible/generated/`, `logs/`) | Keeps generated and runtime noise out of version control |

Copy `.env.example` to `.env` and adjust values when you need non-default secrets or URLs.
