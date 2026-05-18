#!/usr/bin/env bash
set -euo pipefail

./scripts/lint.sh
./scripts/wait-for-api.sh
./scripts/wait-for-targets.sh
docker compose exec api pytest
./scripts/smoke-test.sh
