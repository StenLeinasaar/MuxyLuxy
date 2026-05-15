#!/usr/bin/env bash
set -euo pipefail

for _ in {1..30}; do
  if python3 - <<'PY'
import socket

ports = {"target1": 2221, "target2": 2222}
for name, port in ports.items():
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            pass
    except OSError:
        raise SystemExit(1)
raise SystemExit(0)
PY
  then
    echo "Targets are ready"
    exit 0
  fi
  sleep 1
done

echo "Targets did not become ready" >&2
exit 1
