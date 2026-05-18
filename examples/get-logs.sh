#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${1:-}"

if [ -z "$RUN_ID" ]; then
  echo "Usage: RUN_ID=<id> $0 <run_id>" >&2
  echo "   or: $0 <run_id>" >&2
  exit 1
fi

TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  TOKEN="$(curl -fsS -X POST http://localhost:8000/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"admin","password":"admin"}' | jq -r .access_token)"
fi

curl -fsS "http://localhost:8000/logs?run_id=${RUN_ID}" \
  -H "Authorization: Bearer $TOKEN"
