#!/usr/bin/env bash
set -euo pipefail

for i in {1..30}; do
  if curl -fsS http://localhost:8000/healthz >/dev/null; then
    echo "API is ready"
    exit 0
  fi
  sleep 1
done

echo "API did not become ready" >&2
exit 1
