#!/usr/bin/env bash
set -euo pipefail

# Role paths in PUT /roles must exist on the machine running the API.
# - Docker API (default): /opt/ansible/roles/... inside the container
# - Local API: set ROLLER_ROLES_ROOT to your repo's roles dir, e.g.
#     export ROLLER_ROLES_ROOT="$(pwd)/ansible/roles"
#   (from repo root), or use: make e2e-local
ROLLER_ROLES_ROOT="${ROLLER_ROLES_ROOT:-/opt/ansible/roles}"

ROLLER_SSH_KEY_PATH="${ROLLER_SSH_KEY_PATH:-/opt/roller/ssh/id_rsa}"

TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  TOKEN="$(curl -fsS -X POST http://localhost:8000/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"admin","password":"admin"}' | jq -r .access_token)"
fi

put_role() {
  local name="$1" description="$2"
  local path="${ROLLER_ROLES_ROOT%/}/${name}"
  curl -fsS -X PUT "http://localhost:8000/roles/${name}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg path "$path" --arg desc "$description" '{path: $path, description: $desc}')"
}

curl -fsS -X PUT http://localhost:8000/targets/target1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg host "target1" \
    --arg user "ansible" \
    --arg key "$ROLLER_SSH_KEY_PATH" \
    '{
      host: $host,
      port: 22,
      username: $user,
      auth_type: "ssh_key",
      ssh_private_key_path: $key,
      python_interpreter: "/usr/bin/python3"
    }')"

curl -fsS -X PUT http://localhost:8000/targets/target2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg host "target2" \
    --arg user "ansible" \
    --arg key "$ROLLER_SSH_KEY_PATH" \
    '{
      host: $host,
      port: 22,
      username: $user,
      auth_type: "ssh_key",
      ssh_private_key_path: $key,
      python_interpreter: "/usr/bin/python3"
    }')"

put_role base "Base host setup"
put_role motd "Manage message of the day"
put_role packages "Install demo packages"
