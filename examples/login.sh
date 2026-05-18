#!/usr/bin/env bash
set -euo pipefail

curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
