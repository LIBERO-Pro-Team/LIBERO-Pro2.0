#!/usr/bin/env bash
set -euo pipefail

umask 077
root_dir="$(cd "$(dirname "$0")" && pwd)"
prefix="${1:-${LIBERO_PRO_CONDA_PREFIX:-${HOME}/.conda/envs/libero-pro2}}"
host="${LIBERO_REMOTE_HOST:-127.0.0.1}"
port="${LIBERO_REMOTE_PORT:-8000}"
public_url="${LIBERO_REMOTE_PUBLIC_URL:-http://127.0.0.1:${port}}"
gpu_id="${LIBERO_PRO_GPU_ID:-0}"
egl_device_id="${LIBERO_PRO_EGL_DEVICE_ID:-0}"

[[ -x "$prefix/bin/python" ]] || {
  echo "The Conda environment is missing: $prefix" >&2
  exit 1
}
[[ "$host" =~ ^[0-9A-Fa-f:.]+$ ]] || {
  echo "LIBERO_REMOTE_HOST must be an IP address." >&2
  exit 1
}
[[ "$port" =~ ^[0-9]+$ ]] && ((port >= 1 && port <= 65535)) || {
  echo "LIBERO_REMOTE_PORT must be between 1 and 65535." >&2
  exit 1
}
[[ "$public_url" =~ ^https?://[^[:space:]]+$ ]] || {
  echo "LIBERO_REMOTE_PUBLIC_URL must be an http:// or https:// URL." >&2
  exit 1
}
if [[ -e "$root_dir/server.env" || -e "$root_dir/client.env" ]]; then
  echo "Refusing to overwrite server.env or client.env; remove them explicitly to rotate credentials." >&2
  exit 1
fi

"$prefix/bin/python" - \
  "$root_dir" "$prefix" "$host" "$port" "$public_url" "$gpu_id" "$egl_device_id" <<'PY'
import hashlib
import json
import os
import secrets
import shlex
import sys
from pathlib import Path


root = Path(sys.argv[1]).resolve()
prefix, host, port, public_url, gpu_id, egl_device_id = sys.argv[2:]
baseline = json.loads((root / "SOURCE_BASELINE.json").read_text(encoding="utf-8"))
service_root = root / "service-source"
simulator_root = root / "simulator-source"
manifest = service_root / "assets" / "task_manifest.json"
bddl_root = service_root / "assets" / "bddl" / "libero-pro2.0-169-v1"
for required in (service_root, simulator_root, manifest, bddl_root):
    if not required.exists():
        raise SystemExit(f"Required delivery path is missing: {required}")

runtime = root / "runtime"
logs = root / "logs"
config_root = runtime / "libero-config"
runtime.mkdir(exist_ok=True)
logs.mkdir(exist_ok=True)
config_root.mkdir(exist_ok=True)

api_key = secrets.token_urlsafe(32)
api_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
server_values = {
    "LIBERO_PRO_CONDA_PREFIX": prefix,
    "LIBERO_PRO_ROOT": str(simulator_root),
    "LIBERO_PRO_COMMIT": baseline["simulator_commit"],
    "LIBERO_REMOTE_COMMIT": baseline["service_commit"],
    "LIBERO_REMOTE_BACKEND": "libero",
    "LIBERO_REMOTE_HOST": host,
    "LIBERO_REMOTE_PORT": port,
    "LIBERO_REMOTE_AUTHENTICATION_REQUIRED": "true",
    "LIBERO_REMOTE_API_KEY_HASHES": json.dumps(
        {api_hash: "local-account"}, separators=(",", ":")
    ),
    "LIBERO_REMOTE_RESULT_SIGNING_KEY": secrets.token_hex(32),
    "LIBERO_REMOTE_ALLOW_DIRECT_SESSIONS": "true",
    "LIBERO_REMOTE_MAX_SESSIONS": os.environ.get("LIBERO_REMOTE_MAX_SESSIONS", "1"),
    "LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER": os.environ.get(
        "LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER", "1"
    ),
    "LIBERO_REMOTE_WORKER_TIMEOUT_SECONDS": os.environ.get(
        "LIBERO_REMOTE_WORKER_TIMEOUT_SECONDS", "120"
    ),
    "LIBERO_REMOTE_SESSION_IDLE_TIMEOUT_SECONDS": os.environ.get(
        "LIBERO_REMOTE_SESSION_IDLE_TIMEOUT_SECONDS", "900"
    ),
    "LIBERO_REMOTE_CLEANUP_INTERVAL_SECONDS": os.environ.get(
        "LIBERO_REMOTE_CLEANUP_INTERVAL_SECONDS", "30"
    ),
    "LIBERO_REMOTE_SCHEDULER_DB_PATH": str(runtime / "scheduler.sqlite3"),
    "LIBERO_REMOTE_TASK_MANIFEST": str(manifest),
    "LIBERO_REMOTE_BDDL_ROOT": str(bddl_root),
    "LIBERO_REMOTE_IMAGE_DIGEST": "",
    "LIBERO_CONFIG_PATH": str(config_root),
    "MUJOCO_GL": "egl",
    "PYOPENGL_PLATFORM": "egl",
    "CUDA_VISIBLE_DEVICES": gpu_id,
    "MUJOCO_EGL_DEVICE_ID": egl_device_id,
    "PYTHONUNBUFFERED": "1",
}
client_values = {
    "LIBERO_REMOTE_URL": public_url,
    "LIBERO_REMOTE_API_KEY": api_key,
}


def write_environment(path: Path, values: dict) -> None:
    content = "".join(f"{key}={shlex.quote(str(value))}\n" for key, value in values.items())
    with path.open("w", encoding="utf-8", newline="\n") as output:
        output.write(content)
    path.chmod(0o600)


write_environment(root / "server.env", server_values)
write_environment(root / "client.env", client_values)
config_content = "\n".join(
    [
        f"assets: {json.dumps(str(simulator_root / 'libero' / 'libero' / 'assets'))}",
        f"bddl_files: {json.dumps(str(bddl_root))}",
        f"benchmark_root: {json.dumps(str(simulator_root / 'libero' / 'libero'))}",
        f"datasets: {json.dumps(str(simulator_root / 'libero' / 'datasets'))}",
        f"init_states: {json.dumps(str(simulator_root / 'libero' / 'libero' / 'init_files'))}",
        "",
    ]
)
with (config_root / "config.yaml").open("w", encoding="utf-8", newline="\n") as output:
    output.write(config_content)
PY

chmod 600 "$root_dir/server.env" "$root_dir/client.env"
echo "Created server.env and client.env with mode 0600. Keep both files private."
