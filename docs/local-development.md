# Local development

This note explains how we run the stack locally today and why those choices were made.

## Why Docker Compose instead of Kubernetes (for example Kind local cluster)

For **phase 1**, the local surface area is small: a single API process and one Postgres instance. Docker Compose matches that shape with minimal moving parts.

**Reasons Compose fits right now**

- **Bootstrap cost** — No cluster lifecycle (creating a Kind node, loading images into the cluster, waiting for core DNS, or maintaining Helm/Kustomize overlays) just to run two containers.
- **Iteration speed** — Rebuild and restart map cleanly to `docker compose up --build`. Fewer layers between “change code” and “hit `/healthz`”.
- **Operational honesty** — We are not yet validating Kubernetes-specific behavior (ingress controllers, pod scheduling, resource quotas, CRDs). A Kind cluster would add ceremony without giving us new signal for this stage.
- **Onboarding** — One file (`docker-compose.yml`) and the Docker Desktop (or Engine) workflow most contributors already have.

**When Kind or another local Kubernetes cluster becomes worth it**

- We need **prod-parity** orchestration (multiple replicas, probes as deployed, service mesh, operators).
- We outgrow Compose networking or secrets management and want to exercise the **same manifests** used in staging or production.
- We add components that assume **Kubernetes APIs** or multi-namespace layouts.

Until then, Compose keeps local dev **simple, fast, and easy to reason about**.

## Why bind-mount `.ansible/` and `logs/` (and a named volume for Postgres)

The API container uses **relative paths** for Ansible-related directories (`ANSIBLE_ROOT=.ansible`, and so on) with a working directory of `/app` in the image.

**Bind mounts for `.ansible/` and `logs/`**

- **Host visibility** — Generated playbooks, roles materialized under `.ansible/`, and log files under `logs/` appear directly under the **repository root** on your machine. You can open, diff, and delete them with normal editor and shell tools.
- **Alignment with `.gitignore`** — We ignore volatile paths such as `.ansible/generated/` and `logs/` while keeping the layout predictable for everyone who runs Compose from the repo root.
- **Same mental model as “run from project root”** — Compose bind-mounts `./.ansible` → `/app/.ansible` and `./logs` → `/app/logs`, so environment variables stay short and relative without hard-coding macOS or Linux absolute paths.

**Named volume for Postgres data**

- Database files under `/var/lib/postgresql/data` are **not** meant to be hand-edited from the host file tree. A Docker **named volume** lets the engine manage performance and lifecycle while keeping data out of Git by default.
- On Docker Desktop for Mac, named volume data lives **inside the Linux VM** backing Docker, not as a normal folder next to your clone. That is acceptable for Postgres because we interact through SQL and backups, not by browsing raw files in the repo.

Together, this split means: **opaque, engine-managed storage for the database**; **transparent, repo-local trees for Ansible artifacts and logs** you care about during development.
