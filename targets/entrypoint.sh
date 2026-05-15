#!/usr/bin/env bash
set -euo pipefail

mkdir -p /var/run/sshd
ssh-keygen -A
exec /usr/sbin/sshd -D -e
