#!/usr/bin/env bash
set -euo pipefail

# Wait until the HTTP API responds with a healthy /healthz (including database).

ROLLER_API_URL="${ROLLER_API_URL:-http://localhost:8000}"
ROLLER_API_URL="${ROLLER_API_URL%/}"
health_url="${ROLLER_API_URL}/healthz"

echo "Waiting for API at ${health_url} ..." >&2

for i in $(seq 1 60); do
  if curl -fsS "$health_url" 2>/dev/null | python3 -c "
import json, sys

try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(1)
if data.get('status') != 'ok' or data.get('database') != 'ok':
    sys.exit(1)
"; then
    echo "API is ready (status ok, database ok)." >&2
    exit 0
  fi
  sleep 1
done

echo "API did not become ready within 60s (${health_url})." >&2
exit 1
