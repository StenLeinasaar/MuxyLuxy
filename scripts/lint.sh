#!/usr/bin/env bash
set -euo pipefail

docker compose exec api ruff check .
docker compose exec api ruff format --check .
