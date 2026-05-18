#!/usr/bin/env bash
set -euo pipefail

docker compose exec api ssh \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  -i /opt/roller/ssh/id_rsa \
  ansible@target1 whoami

docker compose exec api ssh \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  -i /opt/roller/ssh/id_rsa \
  ansible@target2 whoami
