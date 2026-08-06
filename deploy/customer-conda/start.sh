#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$root_dir/_runtime.sh"
load_server_environment

mkdir -p "$runtime_dir" "$logs_dir"
lock_dir="$runtime_dir/start.lock"
if ! mkdir "$lock_dir" 2>/dev/null; then
  echo "Another start operation is already in progress." >&2
  exit 1
fi
trap 'rmdir "$lock_dir" 2>/dev/null || true' EXIT

if pid="$(current_service_pid)"; then
  echo "Service is already running (PID $pid)."
  exit 0
fi
clear_process_metadata

server="$LIBERO_PRO_CONDA_PREFIX/bin/libero-remote-server"
[[ -x "$server" ]] || {
  echo "Service executable is missing: $server" >&2
  exit 1
}

cd "$bundle_root"
nohup "$server" >>"$logs_dir/server.log" 2>&1 </dev/null &
pid="$!"
for _ in $(seq 1 20); do
  starttime="$(process_starttime "$pid" 2>/dev/null || true)"
  [[ -n "$starttime" ]] && break
  sleep 0.05
done
if [[ -z "${starttime:-}" ]] || ! kill -0 "$pid" 2>/dev/null; then
  echo "Service exited during startup. See $logs_dir/server.log." >&2
  exit 1
fi

umask 077
printf '%s\n' "$pid" > "$pid_file.tmp"
printf '%s\n' "$starttime" > "$starttime_file.tmp"
mv -f -- "$pid_file.tmp" "$pid_file"
mv -f -- "$starttime_file.tmp" "$starttime_file"
echo "Service is running (PID $pid)."
