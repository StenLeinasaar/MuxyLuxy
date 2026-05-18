#!/usr/bin/env bash
set -euo pipefail

mkdir -p ssh

if [ ! -f ssh/id_rsa ]; then
  ssh-keygen -t rsa -b 4096 -N "" -f ssh/id_rsa
fi

chmod 600 ssh/id_rsa
chmod 644 ssh/id_rsa.pub
