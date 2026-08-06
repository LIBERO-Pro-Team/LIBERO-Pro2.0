#!/usr/bin/env bash

bundle_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime_dir="$bundle_root/runtime"
logs_dir="$bundle_root/logs"
pid_file="$runtime_dir/server.pid"
starttime_file="$runtime_dir/server.starttime"

load_server_environment() {
  [[ -f "$bundle_root/server.env" ]] || {
    echo "server.env is missing; run configure.sh first." >&2
    return 1
  }
  set -a
  # shellcheck disable=SC1091
  source "$bundle_root/server.env"
  set +a
  [[ -n "${LIBERO_PRO_CONDA_PREFIX:-}" ]] || {
    echo "LIBERO_PRO_CONDA_PREFIX is missing from server.env." >&2
    return 1
  }
}

process_starttime() {
  local pid="$1"
  [[ -r "/proc/$pid/stat" ]] || return 1
  awk '{print $22}' "/proc/$pid/stat"
}

current_service_pid() {
  [[ -s "$pid_file" && -s "$starttime_file" ]] || return 1
  local pid expected_starttime actual_starttime
  pid="$(<"$pid_file")"
  expected_starttime="$(<"$starttime_file")"
  [[ "$pid" =~ ^[0-9]+$ && "$expected_starttime" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  actual_starttime="$(process_starttime "$pid")" || return 1
  [[ "$actual_starttime" == "$expected_starttime" ]] || return 1
  printf '%s\n' "$pid"
}

clear_process_metadata() {
  rm -f -- "$pid_file" "$starttime_file"
}
