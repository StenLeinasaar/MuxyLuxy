# Architecture

Phase 1 is a **local Docker Compose stack**: one API, one database, and two disposable **SSH targets** used to exercise Ansible-style workflows later.

## Runtime components

| Service   | Role | Notes |
|-----------|------|--------|
| `postgres` | Primary datastore | Postgres 16; Compose **healthcheck** gates `api` startup. |
| `api` | HTTP control plane | FastAPI + Uvicorn on **8000**; bind-mounts `./ansible` and `./logs` into `/app`. |
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
