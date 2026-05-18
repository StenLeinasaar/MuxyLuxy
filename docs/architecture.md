# Architecture

Phase 1 is a **local Docker Compose stack**: one API, one database, and two disposable **SSH targets** used to exercise Ansible-style workflows later.

## Runtime components

| Service   | Role | Notes |
|-----------|------|--------|
| `postgres` | Primary datastore | Postgres 16; Compose **healthcheck** gates `api` startup. |
| `api` | HTTP control plane | FastAPI + Uvicorn on **8000**; bind-mounts `./ansible` and `./logs` into `/app`. |
| `prometheus` | Metrics TSDB + UI | **Prometheus 2.55** scrapes `http://api:8000/metrics` (see `prometheus/prometheus.yml`). Published on host **9090** (`PROMETHEUS_PORT` overrides). TSDB uses named volume `prometheus_data`. |
| `target1`, `target2` | SSH endpoints | Same image; **sshd** on 22 inside the container, published as **2221** and **2222** on the host so both can run at once. |

## `targets/` image

Purpose: a **minimal Linux SSH server** that looks like a typical Ansible-managed host.

- **Base:** Debian Bookworm slim — straightforward `apt` packages and glibc, close to many servers.
- **Packages:** `openssh-server`, `python3`, `sudo` — SSH access, remote Python if playbooks need it, privilege escalation tests without extra images.
- **User:** `ansible` with **passwordless sudo** (`/etc/sudoers.d/ansible`) so local playbooks can validate become/become_user flows without interactive sudo.
- **Config:** `targets/sshd_config` is copied into the image so behavior is explicit and reviewable (not only distro defaults).
- **Entrypoint:** Generates host keys if missing, runs **sshd in foreground** (`-D`) so the container lifecycle matches the SSH process.

## Data and repo boundaries

- **Postgres data:** named volume (engine-managed; not in the Git tree).
- **Ansible tree + logs on host:** bind mounts keep generated content and logs under the repo for inspection; see `docs/local-development.md`.

## Network shape (local)

Traffic is **flat Compose networking** between services. From the **host**, smoke checks use **localhost** to the published API and SSH ports only—no assumption that the host can resolve Docker service DNS names.

## Observability (Prometheus)

The API exposes **`GET /metrics`** (no auth) in Prometheus text exposition format via `prometheus-client`.

| Metric | Type | Meaning |
|--------|------|--------|
| `ansible_roller_runs_total` | Counter | `status` label: `successful` or `failed`. Counts terminal background runs (including pre-flight failures such as missing target/role). |
| `ansible_roller_active_runs` | Gauge | Runs currently inside the worker path after `in_progress` (ansible-playbook executing or file prep in the same block). |
| `ansible_roller_run_duration_seconds` | Histogram | Wall time from `in_progress` commit through worker completion for that run. |
| `ansible_roller_api_requests_total{method,path}` | Counter | Per-request HTTP counts (labels reflect the literal URL path). |

### Why both in-repo instrumentation and a Prometheus container?

They answer different questions and **cannot be collapsed into one component**:

1. **`service/app/metrics/` (and `prometheus-client` in the API)** — This is **inside the application process**. It defines the metric families, updates them when runs finish and when HTTP requests are handled, and serves the current values at **`GET /metrics`**. Prometheus text over HTTP is just an **export format**; something in the app must still implement counters, gauges, and histograms and expose that endpoint.

2. **`prometheus/prometheus.yml` and the Compose `prometheus` service** — This is a **separate long-lived scraper and time-series database**. It periodically **pulls** `/metrics`, **stores** history, and gives you the **9090** UI, alerting integrations, and queries over past data. The API process does not (and should not) try to duplicate that storage and query engine.

**Why not only the app?** You can run with **just the API**: `curl` or tests can read `/metrics`, but you get **no retention**, no multi-target scraping, and no Prometheus query model unless you add something else later.

**Why not only Prometheus?** A Prometheus server **does not** run your Python code or observe your handlers. With no in-app instrumentation, `/metrics` would be empty or unrelated defaults—there would be **nothing meaningful to scrape**.

So the usual split is: **instrument the app** (this repo: `app/metrics/prometheus.py`), **optionally run Prometheus** (this repo: `prometheus/` + Compose) to scrape and retain that stream.

**Compose scraping** — With `docker compose up`, Prometheus scrapes the API on the default bridge network. On the host, open **http://localhost:9090** → **Status → Targets** to confirm `ansible-roller-api` is **UP**. You can still hit **`GET http://localhost:8000/metrics`** directly without running Prometheus.
