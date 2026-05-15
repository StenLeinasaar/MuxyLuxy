#!/usr/bin/env bash
set -euo pipefail

curl -fsS http://localhost:8000/healthz | grep -q "ok"
echo "API health check passed"

python3 - <<'PY'
import socket

ports = {"target1": 2221, "target2": 2222}
for name, port in ports.items():
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=3):
            pass
    except OSError as exc:
        raise SystemExit(f"{name} (localhost:{port}) is not reachable: {exc}") from exc
print("Target SSH ports reachable: target1 -> 2221, target2 -> 2222")
PY
