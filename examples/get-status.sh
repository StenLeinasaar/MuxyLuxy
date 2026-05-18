#!/usr/bin/env bash
set -euo pipefail

TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  TOKEN="$(curl -fsS -X POST http://localhost:8000/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"admin","password":"admin"}' | jq -r .access_token)"
fi

curl -fsS "http://localhost:8000/status?limit=20" \
  -H "Authorization: Bearer $TOKEN"
