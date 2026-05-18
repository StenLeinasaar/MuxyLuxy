#!/usr/bin/env bash
set -euo pipefail

# Basic API checks: health, auth, unauthenticated denial, CRUD-ish flows, and local SSH targets.

ROLLER_API_URL="${ROLLER_API_URL:-http://localhost:8000}"
ROLLER_API_URL="${ROLLER_API_URL%/}"
ROLLER_SSH_KEY_PATH="${ROLLER_SSH_KEY_PATH:-/opt/roller/ssh/id_rsa}"
# Role path must exist inside the API container (Compose mounts ./ansible -> /opt/ansible).
ROLLER_SMOKE_ROLE_PATH="${ROLLER_SMOKE_ROLE_PATH:-/opt/ansible/roles/base}"

code="$(curl -sS -o /dev/null -w "%{http_code}" "${ROLLER_API_URL}/targets" || true)"
if [ "$code" != "401" ]; then
  echo "Expected 401 for unauthenticated GET /targets, got HTTP ${code}" >&2
  exit 1
fi
echo "Unauthenticated request rejected (401)"

curl -fsS "${ROLLER_API_URL}/healthz" | python3 -c "
import json, sys

data = json.load(sys.stdin)
assert data.get('status') == 'ok', data
assert data.get('database') == 'ok', data
print('API health check passed (status + database)')
"

TOKEN="$(curl -fsS -X POST "${ROLLER_API_URL}/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' | jq -r .access_token)"

test "$TOKEN" != "null"
echo "Login passed"

curl -fsS "${ROLLER_API_URL}/me" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert data.get('username') == 'admin', data
print('GET /me passed')
"

SMOKE_TARGET="smoke_tmp_target"
curl -fsS -X PUT "${ROLLER_API_URL}/targets/${SMOKE_TARGET}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg host "127.0.0.1" \
    --arg user "ansible" \
    --arg key "$ROLLER_SSH_KEY_PATH" \
    '{
      host: $host,
      port: 65534,
      username: $user,
      auth_type: "ssh_key",
      ssh_private_key_path: $key,
      python_interpreter: "/usr/bin/python3"
    }')" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert data.get('name') == '${SMOKE_TARGET}', data
print('PUT target (upsert) passed')
"

curl -fsS "${ROLLER_API_URL}/targets" \
  -H "Authorization: Bearer $TOKEN" | jq -e --arg n "$SMOKE_TARGET" '.[] | select(.name == $n) | .host == "127.0.0.1"' >/dev/null
echo "GET targets includes smoke target"

curl -fsS -o /dev/null -w "%{http_code}" -X DELETE "${ROLLER_API_URL}/targets/${SMOKE_TARGET}" \
  -H "Authorization: Bearer $TOKEN" | grep -qx 204

curl -fsS "${ROLLER_API_URL}/targets" \
  -H "Authorization: Bearer $TOKEN" | jq -e --arg n "$SMOKE_TARGET" 'all(.[]; .name != $n)' >/dev/null
echo "DELETE target + list verification passed"

SMOKE_ROLE="smoke_tmp_role"
curl -fsS -X PUT "${ROLLER_API_URL}/roles/${SMOKE_ROLE}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg path "$ROLLER_SMOKE_ROLE_PATH" '{path: $path, description: "smoke CRUD"}')" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert data.get('name') == '${SMOKE_ROLE}', data
assert data.get('enabled') is True, data
print('PUT role (upsert) passed')
"

curl -fsS -o /dev/null -w "%{http_code}" -X DELETE "${ROLLER_API_URL}/roles/${SMOKE_ROLE}" \
  -H "Authorization: Bearer $TOKEN" | grep -qx 204

curl -fsS "${ROLLER_API_URL}/roles" \
  -H "Authorization: Bearer $TOKEN" | jq -e --arg n "$SMOKE_ROLE" '.[] | select(.name == $n) | .enabled == false' >/dev/null
echo "DELETE role (soft) + list verification passed"

curl -fsS "${ROLLER_API_URL}/targets" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert isinstance(data, list), data
print('List targets passed')
"

curl -fsS "${ROLLER_API_URL}/roles" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert isinstance(data, list), data
print('List roles passed')
"

curl -fsS "${ROLLER_API_URL}/status?limit=20" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert isinstance(data, list), data
print('Status endpoint passed')
"

python3 - <<'PY'
import socket

ports = {"target1": 2221, "target2": 2222}
for name, port in ports.items():
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=3):
            pass
    except OSError as exc:
        raise SystemExit(f"{name} (localhost:{port}) is not reachable: {exc}") from exc
print("Target SSH ports reachable: target1 -> 2221, target2 -> 2222")
PY
