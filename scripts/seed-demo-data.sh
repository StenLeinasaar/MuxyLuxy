#!/usr/bin/env bash
set -euo pipefail

TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  TOKEN="$(curl -fsS -X POST http://localhost:8000/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"admin","password":"admin"}' | jq -r .access_token)"
fi

curl -fsS -X PUT http://localhost:8000/targets/target1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "target1",
    "port": 22,
    "username": "ansible",
    "auth_type": "ssh_key",
    "ssh_private_key_path": "/opt/roller/ssh/id_rsa",
    "python_interpreter": "/usr/bin/python3"
  }'

curl -fsS -X PUT http://localhost:8000/targets/target2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "target2",
    "port": 22,
    "username": "ansible",
    "auth_type": "ssh_key",
    "ssh_private_key_path": "/opt/roller/ssh/id_rsa",
    "python_interpreter": "/usr/bin/python3"
  }'

curl -fsS -X PUT http://localhost:8000/roles/base \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/opt/ansible/roles/base",
    "description": "Base host setup"
  }'

curl -fsS -X PUT http://localhost:8000/roles/motd \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/opt/ansible/roles/motd",
    "description": "Manage message of the day"
  }'

curl -fsS -X PUT http://localhost:8000/roles/packages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/opt/ansible/roles/packages",
    "description": "Install demo packages"
  }'
