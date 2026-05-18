#!/usr/bin/env bash
set -euo pipefail

curl -fsS http://localhost:8000/healthz | python3 -c "
import json, sys

data = json.load(sys.stdin)
assert data.get('status') == 'ok', data
assert data.get('database') == 'ok', data
print('API health check passed (status + database)')
"

TOKEN="$(curl -fsS -X POST http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' | jq -r .access_token)"

test "$TOKEN" != "null"
echo "Login passed"

curl -fsS http://localhost:8000/targets \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert isinstance(data, list), data
print('List targets passed')
"

curl -fsS http://localhost:8000/roles \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert isinstance(data, list), data
print('List roles passed')
"

curl -fsS "http://localhost:8000/status?limit=20" \
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
