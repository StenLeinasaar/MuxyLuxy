# Security

This project is **local lab software**. The controls below match the current codebase and Compose stack; they are **not** a complete production threat model.

## JWT

- **Library:** `python-jose` for encode/decode.
- **Algorithm:** Configurable (`JWT_ALGORITHM`, default **HS256**).
- **Secret:** `JWT_SECRET` (default in `.env.example` is **`change-me`** — unsuitable outside a closed laptop).
- **Claims:** Access tokens include **`sub`** (username) and **`exp`** (expiry). Expiry duration is **`JWT_EXPIRE_MINUTES`**.
- **Verification:** Protected routes decode with the configured secret and algorithm, then load the user from Postgres by **`sub`**. Revocation is **not** implemented (tokens are valid until expiry unless the secret rotates).

## Password hashing

- User passwords are stored as **PBKDF2-HMAC-SHA256** with **per-user salt** and **310,000** iterations (`app/auth.py`). The serialized form embeds algorithm name, iteration count, salt, and hash (URL-safe base64).
- **`secrets.compare_digest`** is used when verifying stored hashes (timing-resistant compare).
- On startup, **`seed_admin_user`** ensures the configured **`ADMIN_USERNAME`** exists and that its hash matches **`ADMIN_PASSWORD`** (updates the hash if env password changed).

## Role allowlisting (registry model)

- Roles are **named entries in the database**, not arbitrary uploads. Each entry points at a **directory on disk** that must already exist inside the API environment.
- **`PUT /roles/{role_name}`** enforces:
  - **Role name** matches `^[A-Za-z0-9_-]+$`.
  - **Resolved path** is **under** `ANSIBLE_ROLES_PATH` (after `expanduser` + `resolve` + `is_relative_to` check — blocks `..` escape from the roles root).
  - Path is a **directory** containing **`tasks/main.yml`**.
- **`DELETE /roles/{name}`** **soft-disables** the role (`enabled: false`); disabled roles cannot be run.

## Path validation

| Surface | Validation |
|---------|------------|
| **Role paths** | Strict: must resolve inside **`ANSIBLE_ROLES_PATH`**, exist, be a directory, contain **`tasks/main.yml`**. |
| **Generated Ansible output** | Each run uses a new subdirectory under **`ANSIBLE_GENERATED_PATH`** (`generate_run_files`). |
| **Run logs** | Written under **`ROLLER_RUN_LOG_DIR`** with filename derived from **`run_id`** (hex from UUID). |
| **Target fields in inventory** | **Host**, **username**, **Python interpreter**, and **private key path** must be single-line values without whitespace or `=` (prevents trivial inventory injection). **Target name** in inventory is restricted to **`^[A-Za-z0-9_.-]+$`**. |
| **SSH private key path on targets** | **Not** root-allow-listed to a specific directory in the API today: any path acceptable to inventory validation can be stored. Operators should treat API users as **trusted** or harden this in production. |

## SSH key handling

- **Host:** `scripts/bootstrap.sh` creates **`./ssh/id_rsa`** (4096-bit RSA, no passphrase) and fixes permissions (**600** private, **644** public). It also guards against Docker creating a **directory** at `ssh/id_rsa` when a bind mount was missing (a common footgun).
- **Compose:** `./ssh` is mounted read-only at **`/opt/roller/ssh_keys`** on `api` and targets. The API **entrypoint** **`install -m 600`** copies **`id_rsa`** to **`/opt/roller/ssh/id_rsa`** because bind-mounted files often have permissive modes OpenSSH refuses.
- **Database:** Targets store **`ssh_private_key_path`** as configured by the client (E2E and seed scripts use **`/opt/roller/ssh/id_rsa`** inside the container).
- **Ansible:** The worker sets **`ANSIBLE_HOST_KEY_CHECKING=False`** for convenience in the lab (see below).

## Known local-environment compromises

These are **intentional or accepted** for developer speed on a single machine:

| Topic | Compromise |
|-------|------------|
| **Default API admin** | `admin` / `admin` unless overridden. |
| **JWT secret default** | Predictable signing key in sample `.env`. |
| **SSH target image** | Known weak **password** for user `ansible` (image build); **password authentication** enabled for the lab. **Do not publish** ports **2221** / **2222** to the internet. |
| **Postgres** | Default user/password in Compose suitable only for local sandboxes. |
| **`GET /metrics`** | **No authentication** — exposes aggregate operational counters to anyone who can reach the port. |
| **Host key checking** | Disabled for Ansible SSH to reduce friction when targets are recreated. |
| **Single admin model** | All authenticated users share the same capabilities (no RBAC); there is only the seeded admin user in typical flows. |

## Production improvements (checklist)

When moving beyond a laptop lab, consider at minimum:

1. **Secrets management** — inject `JWT_SECRET`, DB passwords, and admin bootstrap credentials from a vault or orchestrator secrets (never commit real values).
2. **TLS** — terminate HTTPS at a reverse proxy or ingress; redirect plain HTTP.
3. **AuthN / AuthZ** — multi-user identity, password policies, optional MFA, **role-based access** to targets and Ansible content.
4. **JWT hardening** — short TTLs, refresh flow or session cookies with CSRF protections as appropriate; token revocation list or server-side sessions if needed.
5. **Metrics** — put **`/metrics`** behind auth or network policy (or scrape from a sidecar on loopback only).
6. **SSH** — enforce host key verification or pin keys; prefer **bastion** or **SSH certificate** models; **allow-list** private key paths to a controlled read-only mount.
7. **Network policy** — restrict which pods/VPCs may call the API and which egress the API may use to reach targets.
8. **Auditing** — structured logs for API mutations and run lifecycle; ship to centralized logging.
9. **Supply chain** — pin base images and Python deps; scan images in CI.
10. **Queue workers** — replace in-process background tasks with a **durable queue** so runs survive API restarts and can be rate-limited.

See also [tradeoffs.md](tradeoffs.md) for why some of these are not implemented in the reference stack.
