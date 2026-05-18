# Tradeoffs

Intentional decisions for the **reference stack** (Docker Compose + FastAPI + Postgres + local SSH targets). Alternatives are noted where they matter for production or larger teams.

## Docker Compose vs Kubernetes

| Compose (this repo) | Kubernetes |
|---------------------|------------|
| One YAML file, minimal moving parts for **onboarding** and **CI** | Stronger story for **HA**, rolling deploys, and **multi-tenant** isolation |
| Good for **single-host** labs and smoke/E2E | Higher **operational cost** and cluster prerequisites |
| Networking and volumes are **implicit** and easy to introspect | Requires ingress, DNS, storage classes, and often a **platform team** |

**Why Compose here:** the goal is a **reviewable, runnable** automation lab, not a production orchestration reference. Kubernetes would add ceremony without teaching the Ansible control-plane concepts faster.

## FastAPI background tasks vs queue workers

| `BackgroundTasks` (current `POST /run`) | Queue workers (Celery, RQ, Redis Streams, SQS, etc.) |
|----------------------------------------|------------------------------------------------------|
| **Zero extra infrastructure** | Needs **broker**, workers, and **visibility timeout** handling |
| Runs **in the API process**; lost on crash/restart | Work survives **API restarts**; horizontal **worker scale** |
| **Simple** mental model for a demo API | Better for **fair scheduling**, **retries**, and **backpressure** |

**Why background tasks here:** smallest path to a working **`ansible-playbook`** integration and metrics. Production should assume a **durable queue** and idempotent run bookkeeping.

## Local filesystem logs vs centralized logging

| Bind-mounted `./logs` | Centralized logging (ELK, Loki, CloudWatch, etc.) |
|----------------------|---------------------------------------------------|
| **Immediate** `tail -f` and gitignored artifacts | **Search**, retention policies, and **correlation IDs** across services |
| No extra cost or stack components | Requires **agents**, shipping, and **PII** handling |

**Why filesystem logs:** developers can open a file per `run_id` next to **generated Ansible** under `./ansible/generated/`. Centralized logging is left as an integration exercise.

## Single Postgres vs HA

| One Compose `postgres` service | HA Postgres (Patroni, managed RDS, etc.) |
|--------------------------------|------------------------------------------|
| Easy **reset** (`docker compose down -v`) | **Failover**, backups, and **read replicas** |
| **Single point of failure** | Higher cost and **migration** discipline |

**Why single node:** the database holds **small configuration state** (users, targets, roles, run metadata). The interesting failure modes for this repo are **Ansible and SSH**, not Postgres clustering.

## Role registry vs arbitrary playbook upload

| Registry: DB row + validated path under `roles/` | Upload arbitrary playbooks / zip bundles |
|--------------------------------------------------|----------------------------------------|
| **Tight coupling** to reviewed **git** content in `./ansible` | Flexible for ad-hoc automation |
| **Path traversal** resistance is tractable (`is_relative_to` roles root) | **Large attack surface** (malicious YAML, Jinja, module plugins) |
| Encourages **code review** of roles like any other repo | Harder to **audit** and to sandbox execution |

**Why a registry:** the API selects **known role names** and generates a **small static playbook** template. Arbitrary upload would require **content scanning**, signing, and stronger **process isolation** than a subprocess in the API container.

---

## Decision log

| Date | Decision | Rationale | Alternatives considered |
|------|----------|-----------|---------------------------|
| 2026-05-15 | Local dev via Docker Compose; bind mounts for `./ansible/` and `./logs/`, named volume for Postgres | Low ceremony; host-visible artifacts; DB data managed by Docker | Kubernetes / Kind; bind-mounting Postgres data into the repo |
| 2026-05-15 | Two Compose services `target1` / `target2`, same image, host ports **2221** / **2222** | Multiple hosts without port clashes; one Dockerfile | Single target; dynamic scale with random ports |
| 2026-05-15 | Target image: Debian slim + `openssh-server`, `python3`, `sudo`; user `ansible` with NOPASSWD sudo | Matches common Ansible targets | Alpine musl; cloud-only VMs |
| 2026-05-15 | Smoke: `curl` + `python3` TCP; separate **wait** scripts | Validates published ports; avoids `nc` portability | In-container-only checks; `docker compose ps` only |

## Open questions

Questions a reviewer or adopter might ask next — not decided in this repo, but they shape how you would extend the control plane.

### Ansible layout, templates, and multi-target configuration

- **Role taxonomy:** Is it more efficient to keep many small roles (one concern each) under `ansible/roles/` and compose behavior via **run order** and API conventions, or to bundle “profiles” (e.g. `web`, `db`) as single roles that wrap many tasks internally?
- **Templates vs the generated playbook:** The API today emits a **thin playbook** that applies one role by name. How would you introduce **parameterized** runs (extra vars, tags, limits) without abandoning the safety of the registry model — separate API fields, Jinja-only role defaults, or external **Ansible Vault** / config repos?
- **Shared baseline:** If every host needs the same baseline (`base`, users, sshd, packages), should that be **implicit** (always prepended) or **explicit** (callers always pass two roles / two runs)? What is the cleanest contract for operators vs the API?

### Automating target creation (machines, images, “cattle”)

- **Provisioning loop:** The API only registers **existing** SSH endpoints (`host`, `port`, key path). What is the best way to **automate adding machines** — cloud APIs + Terraform, **Docker** or **Incus** APIs, or a dedicated “provisioner” worker that creates a VM/container then calls **`PUT /targets`** when SSH is ready?
- **Image / spec in the API:** If `PUT /targets` accepted something like “image ID + network profile” instead of raw `ansible_host`, you would need a **pluggable backend** (hypervisor, CSP SDK) and likely **async** provisioning with state machines (`provisioning` → `ready` → `failed`). Is that still the same product as “Ansible Roller,” or a separate **fleet** service that this API only triggers runs against?
- **Chicken and egg:** New hosts often need a **bootstrap** role (users, keys, sudo) before they match the assumptions of later roles. Do you bake that into the **image** (cloud-init, Packer), run a **one-shot** bootstrap playbook out-of-band, or extend the API with a **first-run** / **bootstrap** role flag that runs under stricter timeouts and logging?

### Operations and safety (still open at lab scale)

- **Hosted deployment:** Topology, identity provider (OIDC vs API tokens), and whether runs should execute in **Firecracker**/VM sandboxes vs only in the API container’s subprocess.
- **Secrets:** Today targets store a **filesystem path** to a private key. How should keys and vault passwords be injected for production — sidecar mounts, short-lived SSH certs, HashiCorp Vault, CSP instance roles?
