#!/usr/bin/env bash
set -euo pipefail

# Python unit and API tests (pytest in the api service container).

docker compose exec -T api pytest
