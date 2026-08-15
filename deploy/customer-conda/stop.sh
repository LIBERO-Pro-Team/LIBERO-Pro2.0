#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$root_dir/_runtime.sh"

if ! pid="$(current_service_pid)"; then
  clear_process_metadata
  echo "Service is not running."
  exit 0
fi

kill -TERM "$pid"
timeout_seconds="${LIBERO_REMOTE_STOP_TIMEOUT_SECONDS:-30}"
deadline=$((SECONDS + timeout_seconds))
while kill -0 "$pid" 2>/dev/null && ((SECONDS < deadline)); do
  sleep 0.1
done
if kill -0 "$pid" 2>/dev/null; then
  kill -KILL "$pid"
  for _ in $(seq 1 20); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.05
  done
fi
clear_process_metadata
echo "Service stopped (PID $pid)."
