#!/usr/bin/env bash
set -euo pipefail

docker compose exec -T api sh -c 'cat > /tmp/inventory.ini && ansible all -i /tmp/inventory.ini -m ping' <<'INVENTORY'
[targets]
target1
target2

[targets:vars]
ansible_user=ansible
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_private_key_file=/opt/roller/ssh/id_rsa
ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
INVENTORY
