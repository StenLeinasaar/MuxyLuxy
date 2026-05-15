# MuxyLuxy

Infrastructure automation engineering.

## What exists today (phase 1)

- **FastAPI service** (`service/`) — minimal app with `GET /healthz`, packaged with `pyproject.toml` (Python 3.12) and a **Dockerfile** that runs Uvicorn on port 8000.
- **Local stack** — `docker-compose.yml` runs **Postgres 16** (with a named volume and healthcheck) and the **api** service; the API waits until Postgres is healthy before starting.
- **Environment** — `.env.example` documents variables; copy to `.env` for overrides. Database URL targets the `postgres` service on the Compose network.
- **Ansible-related paths** — Stored as **paths relative to the API working directory** (`/app` in the container). Compose **bind-mounts** the repo’s `.ansible/` to `/app/.ansible` and `logs/` to `/app/logs`, so when you run Compose from the **repository root**, those directories are the same paths on your machine (see below).
- **Scripts** — `scripts/test.sh`, `scripts/lint.sh` (placeholders), and `scripts/smoke-test.sh` (hits `http://localhost:8000/healthz` once the stack is up).
- **Docs** — Placeholders: `docs/architecture.md`, `docs/security.md`, `docs/tradeoffs.md`, `docs/testing.md`. **Local dev rationale:** `docs/local-development.md` (Compose vs Kind, bind mounts vs named volumes).

### Quick start

```bash
cp .env.example .env   # optional; compose has defaults
docker compose up --build
```

Smoke check (from repo root): `./scripts/smoke-test.sh`

## Repository layout

| Path | Purpose |
|------|---------|
| `docs/` | Documentation |
| `scripts/` | Shell and helper scripts |
| `service/` | Application or service code |
| `ansible/` | Ansible playbooks, roles, inventory (layout TBD) |
| `targets/` | Deployment or build targets |
| `examples/` | Example configurations and snippets |
| `.ansible/` | Local Ansible working tree for the API (roles, generated output); created on disk via Compose bind mount |
| `logs/` | Service log output directory; bind-mounted for the API |

## Decisions so far

| Topic | Choice | Rationale |
|-------|--------|-----------|
| API framework | FastAPI | Async-friendly HTTP API; simple health endpoint for compose/smoke tests |
| Python packaging | `pyproject.toml` + setuptools | Standard install in Docker via `pip install .` |
| Database | Postgres 16 (Alpine) in Compose | Matches SQLAlchemy/psycopg stack declared for later phases |
| API startup order | `depends_on` + Postgres `healthcheck` | Avoids connection races against a not-yet-ready database |
| Ansible paths | Relative paths + bind mounts | Keeps artifacts under the repo root (`.ansible/`, `logs/`) instead of hard-coded `/opt/...` paths, so local dev matches “run from project root” |
| Generated output & logs | Gitignored (`.ansible/generated/`, `logs/`) | Keeps generated and runtime noise out of version control |

Copy `.env.example` to `.env` and adjust values when you need non-default secrets or URLs.
