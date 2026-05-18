#!/usr/bin/env bash
set -euo pipefail

# Host ./ssh is mounted at ssh_keys; copy so we can chmod 600 (OpenSSH rejects loose perms on mounts).
if [[ -f /opt/roller/ssh_keys/id_rsa ]]; then
  mkdir -p /opt/roller/ssh
  install -m 600 /opt/roller/ssh_keys/id_rsa /opt/roller/ssh/id_rsa
fi

alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
