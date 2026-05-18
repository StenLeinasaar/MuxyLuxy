#!/usr/bin/env bash
set -euo pipefail

mkdir -p /var/run/sshd
ssh-keygen -A

mkdir -p /home/ansible/.ssh
if [ -f /opt/roller/ssh/id_rsa.pub ]; then
  cp /opt/roller/ssh/id_rsa.pub /home/ansible/.ssh/authorized_keys
fi
chown -R ansible:ansible /home/ansible/.ssh
chmod 700 /home/ansible/.ssh
if [ -f /home/ansible/.ssh/authorized_keys ]; then
  chmod 600 /home/ansible/.ssh/authorized_keys
fi

exec /usr/sbin/sshd -D -e
