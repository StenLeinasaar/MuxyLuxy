#!/usr/bin/env bash
set -euo pipefail

for i in {1..30}; do
  if curl -fsS http://localhost:8000/healthz | python3 -c "
import json, sys

try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(1)
if data.get('status') != 'ok' or data.get('database') != 'ok':
    sys.exit(1)
"; then
    echo "API is ready (database reachable)"
    exit 0
  fi
  sleep 1
done

echo "API did not become ready" >&2
exit 1
