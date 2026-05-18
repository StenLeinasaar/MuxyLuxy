#!/usr/bin/env bash
set -euo pipefail

# Generate local SSH keys and required local directories/files for Docker Compose
# (bind mounts, logs, generated Ansible output).

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p ssh logs ansible/generated

# Docker bind-mounting a missing path can create directories; ssh-keygen then fails.
if [ -d ssh/id_rsa ]; then
  echo "Removing ssh/id_rsa (directory — usually from an earlier compose mount before keys existed)." >&2
  rm -rf ssh/id_rsa
fi
if [ -d ssh/id_rsa.pub ]; then
  echo "Removing ssh/id_rsa.pub (directory — same bind-mount edge case)." >&2
  rm -rf ssh/id_rsa.pub
fi

# Empty file blocks ssh-keygen
if [ -f ssh/id_rsa ] && [ ! -s ssh/id_rsa ]; then
  rm -f ssh/id_rsa ssh/id_rsa.pub
fi

if [ ! -f ssh/id_rsa ]; then
  ssh-keygen -t rsa -b 4096 -N "" -f ssh/id_rsa
elif [ ! -f ssh/id_rsa.pub ] || [ ! -s ssh/id_rsa.pub ]; then
  ssh-keygen -y -f ssh/id_rsa > ssh/id_rsa.pub.tmp
  mv ssh/id_rsa.pub.tmp ssh/id_rsa.pub
fi

chmod 600 ssh/id_rsa
chmod 644 ssh/id_rsa.pub
