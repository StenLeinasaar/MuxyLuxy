#!/usr/bin/env bash
set -euo pipefail

# Seeding uses ROLLER_ROLES_ROOT (see scripts/seed-demo-data.sh). Defaults suit the
# Dockerized API (/opt/ansible/roles). For a host-run API use: make e2e-local

TOKEN="$(curl -fsS -X POST http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' | jq -r .access_token)"

./scripts/seed-demo-data.sh

RUN_IDS=()
for n in 1 2 3; do
  rid="$(
    curl -fsS -X POST http://localhost:8000/run \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"target_name":"target1","role_name":"motd"}' | jq -r .run_id
  )"
  RUN_IDS+=("$rid")
  echo "Queued run $n: $rid"
done

status_for() {
  local run_id="$1"
  local json="$2"
  echo "$json" | jq -r --arg id "$run_id" '.[] | select(.run_id == $id) | .status'
}

for i in $(seq 1 90); do
  STATUS_JSON="$(curl -fsS -H "Authorization: Bearer $TOKEN" "http://localhost:8000/status")"

  all_successful=true
  any_failed=false
  n=0
  msg="Poll $i:"
  for rid in "${RUN_IDS[@]}"; do
    n=$((n + 1))
    st="$(status_for "$rid" "$STATUS_JSON")"
    msg="$msg run$n=$st"
    if [ "$st" != "successful" ]; then
      all_successful=false
    fi
    if [ "$st" = "failed" ]; then
      any_failed=true
    fi
  done
  echo "$msg"

  if $any_failed; then
    echo "One or more runs failed" >&2
    for rid in "${RUN_IDS[@]}"; do
      st="$(status_for "$rid" "$STATUS_JSON")"
      if [ "$st" = "failed" ]; then
        echo "--- logs for $rid ---" >&2
        curl -fsS -H "Authorization: Bearer $TOKEN" \
          "http://localhost:8000/logs?run_id=$rid" >&2 || true
      fi
    done
    exit 1
  fi

  if $all_successful; then
    echo "All 3 runs completed successfully"
    exit 0
  fi

  sleep 2
done

echo "Runs did not all finish in time" >&2
exit 1
