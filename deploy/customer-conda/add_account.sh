#!/usr/bin/env bash
set -euo pipefail

umask 077
root_dir="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$root_dir/_runtime.sh"

account="${1:-}"
[[ "$account" =~ ^[A-Za-z0-9._-]{1,64}$ ]] || {
  echo "Usage: bash add_account.sh ACCOUNT_ID" >&2
  echo "ACCOUNT_ID may contain letters, digits, dot, underscore, and hyphen." >&2
  exit 1
}
if pid="$(current_service_pid)"; then
  echo "Stop the service before adding an account (running PID $pid)." >&2
  exit 1
fi
load_server_environment
[[ -f "$root_dir/client.env" ]] || {
  echo "client.env is missing; run configure.sh first." >&2
  exit 1
}
client_file="$root_dir/client-$account.env"
[[ ! -e "$client_file" ]] || {
  echo "Refusing to overwrite existing account file: $client_file" >&2
  exit 1
}
set -a
# shellcheck disable=SC1091
source "$root_dir/client.env"
set +a

"$LIBERO_PRO_CONDA_PREFIX/bin/python" - \
  "$root_dir/server.env" "$client_file" "$account" "$LIBERO_REMOTE_URL" <<'PY'
import hashlib
import json
import os
import secrets
import shlex
import sys
from pathlib import Path


server_path = Path(sys.argv[1])
client_path = Path(sys.argv[2])
account = sys.argv[3]
public_url = sys.argv[4]
hashes = json.loads(os.environ["LIBERO_REMOTE_API_KEY_HASHES"])
if account in hashes.values():
    raise SystemExit(f"Account already exists in server.env: {account}")

api_key = secrets.token_urlsafe(32)
api_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
hashes[api_hash] = account
lines = server_path.read_text(encoding="utf-8").splitlines()
replacement = "LIBERO_REMOTE_API_KEY_HASHES=" + shlex.quote(
    json.dumps(hashes, separators=(",", ":"), sort_keys=True)
)
matches = [index for index, line in enumerate(lines) if line.startswith("LIBERO_REMOTE_API_KEY_HASHES=")]
if len(matches) != 1:
    raise SystemExit("server.env must contain exactly one API key hash setting")
lines[matches[0]] = replacement

client_content = "".join(
    (
        f"LIBERO_REMOTE_URL={shlex.quote(public_url)}\n",
        f"LIBERO_REMOTE_API_KEY={shlex.quote(api_key)}\n",
    )
)
with client_path.open("w", encoding="utf-8", newline="\n") as output:
    output.write(client_content)
client_path.chmod(0o600)
temporary = server_path.with_name(f".{server_path.name}.{os.getpid()}.tmp")
try:
    with temporary.open("w", encoding="utf-8", newline="\n") as output:
        output.write("\n".join(lines) + "\n")
    temporary.chmod(0o600)
    os.replace(str(temporary), str(server_path))
except Exception:
    client_path.unlink(missing_ok=True)
    temporary.unlink(missing_ok=True)
    raise
PY

chmod 600 "$root_dir/server.env" "$client_file"
echo "Created $(basename "$client_file") for account $account. Keep it private."
