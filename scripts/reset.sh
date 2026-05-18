#!/usr/bin/env bash
set -euo pipefail

# Destroy the local Compose stack (including volumes) and bring it back up.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

docker compose down -v --remove-orphans
"$ROOT/scripts/bootstrap.sh"
docker compose up -d --build
"$ROOT/scripts/wait-for-api.sh"
"$ROOT/scripts/wait-for-targets.sh"
echo "Local environment reset and ready." >&2
