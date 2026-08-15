#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$root_dir/_runtime.sh"

if pid="$(current_service_pid)"; then
  echo "Service is running (PID $pid)."
  exit 0
fi
echo "Service is not running."
exit 1
